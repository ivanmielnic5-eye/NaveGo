#!/usr/bin/env node
// Patch para expo-task-manager 14.0.9:
// 1. Corrige la fuga de memoria en sTaskCallbacks (get -> remove).
// 2. Evita que la Task muera cuando la app se cierra (onDestroy -> setTaskManager(null)).
// Fail-closed: si el código de la librería cambia, este script falla sin tocar nada.
// Idempotente: si ya está parcheado, no hace nada.
// Aplicación atómica: verifica todo antes de escribir.

const fs = require('fs');
const path = require('path');

const PKG = 'expo-task-manager';
const PKG_VERSION = '14.0.9';
const NODE_MODULES = path.join(__dirname, '..', 'node_modules');
const PKG_PATH = path.join(NODE_MODULES, PKG, 'package.json');
const TASK_SERVICE_PATH = path.join(NODE_MODULES, PKG, 'android', 'src', 'main', 'java', 'expo', 'modules', 'taskManager', 'TaskService.java');
const TASK_MANAGER_MODULE_PATH = path.join(NODE_MODULES, PKG, 'android', 'src', 'main', 'java', 'expo', 'modules', 'taskManager', 'TaskManagerInternalModule.java');

// ── 1. Verificar que el paquete existe ─────────────────────────────────────
if (!fs.existsSync(PKG_PATH)) {
  console.error(`[patch] ${PKG} no encontrado en node_modules. ¿Corriste npm install?`);
  process.exit(1);
}

// ── 2. Verificar versión exacta ────────────────────────────────────────────
const pkg = JSON.parse(fs.readFileSync(PKG_PATH, 'utf8'));
if (pkg.version !== PKG_VERSION) {
  console.error(`[patch] Versión inesperada de ${PKG}: ${pkg.version}. Se esperaba ${PKG_VERSION}. Deteniendo.`);
  process.exit(1);
}

// ── 3. Verificar que ambos archivos existen ────────────────────────────────
if (!fs.existsSync(TASK_SERVICE_PATH)) {
  console.error(`[patch] TaskService.java no encontrado. Ruta: ${TASK_SERVICE_PATH}`);
  process.exit(1);
}
if (!fs.existsSync(TASK_MANAGER_MODULE_PATH)) {
  console.error(`[patch] TaskManagerInternalModule.java no encontrado. Ruta: ${TASK_MANAGER_MODULE_PATH}`);
  process.exit(1);
}

// ── 4. Leer ambos archivos ─────────────────────────────────────────────────
let taskServiceSource = fs.readFileSync(TASK_SERVICE_PATH, 'utf8');
let taskManagerModuleSource = fs.readFileSync(TASK_MANAGER_MODULE_PATH, 'utf8');

// ── 5. PATCH 1: sTaskCallbacks.get -> remove ───────────────────────────────
const PATCH1_ALREADY = 'sTaskCallbacks.remove(eventId)';
const PATCH1_TARGET = 'sTaskCallbacks.get(eventId)';
let patch1Needed = !taskServiceSource.includes(PATCH1_ALREADY);

if (patch1Needed) {
  const count1 = (taskServiceSource.match(new RegExp(PATCH1_TARGET.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g')) || []).length;
  if (count1 !== 1) {
    console.error(`[patch] PATCH1: Se esperaba 1 ocurrencia de "${PATCH1_TARGET}" y se encontraron ${count1}.`);
    process.exit(1);
  }
  taskServiceSource = taskServiceSource.replace(PATCH1_TARGET, PATCH1_ALREADY);
}

// ── 6. PATCH 2: onDestroy -> comentar setTaskManager(null) ─────────────────
const PATCH2_ALREADY = '// mTaskService.setTaskManager(null, getAppScopeKey(), getAppUrl());';
const PATCH2_TARGET = 'mTaskService.setTaskManager(null, getAppScopeKey(), getAppUrl());';
let patch2Needed = !taskManagerModuleSource.includes(PATCH2_ALREADY);

if (patch2Needed) {
  const count2 = (taskManagerModuleSource.match(new RegExp(PATCH2_TARGET.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g')) || []).length;
  if (count2 !== 1) {
    console.error(`[patch] PATCH2: Se esperaba 1 ocurrencia de "${PATCH2_TARGET}" y se encontraron ${count2}.`);
    process.exit(1);
  }
  taskManagerModuleSource = taskManagerModuleSource.replace(PATCH2_TARGET, PATCH2_ALREADY);
}

// ── 7. Si no hace falta ningún parche, salir ───────────────────────────────
if (!patch1Needed && !patch2Needed) {
  console.log(`[patch] ${PKG} ya está parcheado (ambos parches). Nada que hacer.`);
  process.exit(0);
}

// ── 8. Aplicar ambos cambios (solo si llegamos acá sin errores) ────────────
if (patch1Needed) {
  fs.writeFileSync(TASK_SERVICE_PATH, taskServiceSource, 'utf8');
  console.log(`[patch] PATCH1 aplicado: get -> remove en TaskService.java`);
}
if (patch2Needed) {
  fs.writeFileSync(TASK_MANAGER_MODULE_PATH, taskManagerModuleSource, 'utf8');
  console.log(`[patch] PATCH2 aplicado: onDestroy ya no borra el TaskManager.`);
}

// ── 9. Verificación posterior ──────────────────────────────────────────────
const finalTaskService = fs.readFileSync(TASK_SERVICE_PATH, 'utf8');
const finalTaskManagerModule = fs.readFileSync(TASK_MANAGER_MODULE_PATH, 'utf8');
if (!finalTaskService.includes(PATCH1_ALREADY)) {
  console.error(`[patch] Verificación falló: PATCH1 no está presente en TaskService.java.`);
  process.exit(1);
}
if (!finalTaskManagerModule.includes(PATCH2_ALREADY)) {
  console.error(`[patch] Verificación falló: PATCH2 no está presente en TaskManagerInternalModule.java.`);
  process.exit(1);
}

console.log(`[patch] ${PKG} parcheado OK. Ambos parches verificados.`);
