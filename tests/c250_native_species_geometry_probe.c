/* C250: real native C species-map -> verified P3VX/P3IX pair integration.
 * Synthetic host regression and private offline QA only. This is not a
 * source-verified original species mapping or emulator rendering proof. */
#include "species_model_map.h"
#include "verified_geometry_pair.h"
#include <stdio.h>
#include <stdlib.h>

static P3DModelMap map;
static P3DVerifiedGeometryPair pair;

int main(int argc, char **argv) {
    char mapping[1024], vx[1024], ix[1024];
    int species, expected, model;
    unsigned long triangles;
    if (argc != 5) return 2;
    species = atoi(argv[2]);
    expected = atoi(argv[3]);
    triangles = strtoul(argv[4], NULL, 10);
    if (species < 1 || species > P3D_SPECIES_COUNT ||
        expected < -1 || expected >= P3D_RESOURCE_COUNT ||
        triangles > P3D_GEOMETRY_MAX_TRIANGLES) return 2;
    if (snprintf(mapping, sizeof(mapping), "%s/models/species_map.p3sm", argv[1]) >=
        (int)sizeof(mapping)) return 2;
    if (!p3dModelMapLoad(&map, mapping)) {
        fputs("C250 rejected invalid diagnostic P3SM\n", stderr);
        return 1;
    }
    model = p3dModelMapResolve(&map, species - 1);
    if (model != expected) {
        fputs("C250 species/resource binding mismatch\n", stderr);
        return 1;
    }
    if (model == -1) {
        if (triangles != 0) return 2;
        puts("C250 unavailable diagnostic slot: PASS");
        return 0;
    }
    if (!triangles ||
        snprintf(vx, sizeof(vx), "%s/geometry/p%03d.p3vx", argv[1], model) >=
            (int)sizeof(vx) ||
        snprintf(ix, sizeof(ix), "%s/geometry/p%03d.p3ix", argv[1], model) >=
            (int)sizeof(ix)) return 2;
    if (!p3dVerifiedGeometryPairLoad(&pair, vx, ix, (unsigned short)model) ||
        !pair.ready || pair.model != model || pair.triangles != triangles) {
        fputs("C250 native mapped geometry pair rejected\n", stderr);
        return 1;
    }
    /* A failed species reload must clear all previous model geometry. */
    if (p3dVerifiedGeometryPairLoad(&pair, "/missing/c250.p3vx", ix,
                                    (unsigned short)model) ||
        pair.ready || pair.triangles || pair.mesh_count || pair.ix_size) {
        fputs("C250 stale native geometry survived failed reload\n", stderr);
        return 1;
    }
    puts("C250 native species-map/geometry pair and reset: PASS");
    return 0;
}
