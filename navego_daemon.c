#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>

typedef struct {
    char utc[16];
    char fix_status;
    char lat[16];
    char lat_ns;
    char lon[16];
    char lon_ew;
    float sog;
    float cog;
    char date[16];
    int valid;
} NavState;

int parse_gprmc(const char *line, NavState *state) {
    if (strstr(line, "$GPRMC") == NULL) return 0;
    char buffer[256];
    strncpy(buffer, line, sizeof(buffer));
    buffer[sizeof(buffer) - 1] = '\0';
    char *tokens[15];
    int count = 0;
    char *token = strtok(buffer, ",");
    while (token != NULL && count < 15) {
        tokens[count++] = token;
        token = strtok(NULL, ",");
    }
    if (count < 10) return 0;
    strncpy(state->utc, tokens[1], sizeof(state->utc));
    state->fix_status = tokens[2][0];
    strncpy(state->lat, tokens[3], sizeof(state->lat));
    state->lat_ns = tokens[4][0];
    strncpy(state->lon, tokens[5], sizeof(state->lon));
    state->lon_ew = tokens[6][0];
    state->sog = (strlen(tokens[7]) > 0) ? atof(tokens[7]) : 0.0f;
    state->cog = (strlen(tokens[8]) > 0) ? atof(tokens[8]) : 0.0f;
    if (count > 9) {
        strncpy(state->date, tokens[9], sizeof(state->date));
    }
    state->valid = (state->fix_status == 'A') ? 1 : 0;
    return 1;
}

int main() {
    const char *log_path = "/home/ivan/navego_wal.log";
    const char *state_path = "/home/ivan/navego_state.json";

    printf("[C-DAEMON] Iniciando bucle de telemetría a 1Hz...\n");

    while (1) {
        FILE *f = fopen(log_path, "r");
        if (f) {
            char line[256];
            if (fgets(line, sizeof(line), f)) {
                NavState state;
                if (parse_gprmc(line, &state)) {
                    FILE *sf = fopen(state_path, "w");
                    if (sf) {
                        fprintf(sf, "{\"valid\": %d, \"utc\": \"%s\", \"lat\": \"%s %c\", \"lon\": \"%s %c\", \"sog\": %.2f, \"cog\": %.2f, \"date\": \"%s\"}\n",
                                state.valid, state.utc, state.lat, state.lat_ns, state.lon, state.lon_ew, state.sog, state.cog, state.date);
                        fclose(sf);
                    }
                }
            }
            fclose(f);
        }
        usleep(1000000); // Frecuencia de muestreo: 1 Hz
    }
    return 0;
}
