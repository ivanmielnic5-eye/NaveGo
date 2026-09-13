#include <stdio.h>
#include <string.h>
#include <stdlib.h>

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
    FILE *f = fopen("/home/ivan/navego_wal.log", "r");
    if (!f) {
        perror("Error abriendo WAL");
        return 1;
    }
    char line[256];
    if (fgets(line, sizeof(line), f)) {
        NavState state;
        if (parse_gprmc(line, &state)) {
            printf("[C-CORE] Estado procesado con éxito:\n");
            printf("  VALID FIX : %d\n", state.valid);
            printf("  UTC TIME  : %s\n", state.utc);
            printf("  LATITUDE  : %s %c\n", state.lat, state.lat_ns);
            printf("  LONGITUDE : %s %c\n", state.lon, state.lon_ew);
            printf("  SOG       : %.2f nudos\n", state.sog);
            printf("  COG       : %.2f deg\n", state.cog);
            printf("  DATE      : %s\n", state.date);
        } else {
            fprintf(stderr, "Error en parsing de trama.\n");
        }
    }
    fclose(f);
    return 0;
}
