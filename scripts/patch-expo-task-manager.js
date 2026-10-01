#!/usr/bin/env node
// Patch para expo-task-manager 14.0.9: corrige la fuga de memoria en sTaskCallbacks.
// Cambia `sTaskCallbacks.get(eventId)` por `sTaskCallbacks.remove(eventId)`.
// Fail-closed: si el código de la librería cambia, este script falla.

const fs = require('fs');
const path = require('path');

const PKG = 'expo-task-manager';
const PKG_PATH = path.join(__dirname, '..', 'node_modules', PKG, 'package.json');
const TASK_SERVICE_PATH = path.join(
  __dirname,
  '..',
  'node_modules',
  PKG,
  'android',
  'src',
  'main',
  'java',
  'expo',
  'modules',
  'taskManager',
  'TaskService.java'
);

// 1. Verificar que el paquete existe
if (!fs.existsSync(PKG_PATH)) {
  console.error(`[patch] ${PKG} no encontrado en node_modules. ¿Corriste npm install?`);
  process.exit(1);
}

// 2. Verificar versión exacta
const pkg = JSON.parse(fs.readFileSync(PKG_PATH, 'utf8'));
if (pkg.version !== '14.0.9') {
  console.error(`[patch] Versión inesperada de ${PKG}: ${pkg.version}. Se esperaba 14.0.9.`);
  console.error(`[patch] Este parche solo aplica a 14.0.9. Deteniendo.`);
  process.exit(1);
}

// 3. Verificar que el archivo Java existe
if (!fs.existsSync(TASK_SERVICE_PATH)) {
  console.error(`[patch] TaskService.java no encontrado en la ruta esperada.`);
  console.error(`[patch] Ruta: ${TASK_SERVICE_PATH}`);
  process.exit(1);
}

// 4. Leer el archivo
let source = fs.readFileSync(TASK_SERVICE_PATH, 'utf8');

// 5. Idempotencia: si ya está parcheado, salir sin error
const alreadyPatched = 'sTaskCallbacks.remove(eventId)';
const toPatch = 'sTaskCallbacks.get(eventId)';

if (source.includes(alreadyPatched)) {
  console.log(`[patch] ${PKG} ya está parcheado. Nada que hacer.`);
  process.exit(0);
}

// 6. Verificar que la línea a cambiar existe EXACTAMENTE una vez
const occurrences = (source.match(new RegExp(toPatch.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g')) || []).length;
if (occurrences !== 1) {
  console.error(`[patch] Se esperaba 1 ocurrencia de "${toPatch}" y se encontraron ${occurrences}.`);
  console.error(`[patch] El código de ${PKG} cambió. Revisar antes de aplicar el parche.`);
  process.exit(1);
}

// 7. Aplicar el cambio
source = source.replace(toPatch, alreadyPatched);
fs.writeFileSync(TASK_SERVICE_PATH, source, 'utf8');

console.log(`[patch] ${PKG} parcheado OK: get -> remove en TaskService.java`);
