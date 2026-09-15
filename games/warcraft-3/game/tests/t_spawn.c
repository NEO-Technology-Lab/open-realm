#ifdef BZ_TESTS
#include "shared/test.h"
#include "../g_local.h"

TEST(wc3_spawn, map_script_object_filter_keeps_units_and_items_only) {
    T_ASSERT(G_TestMapObjectCreatedByMapScript(MAKEFOURCC('o', 'p', 'e', 'o')));
    T_ASSERT(G_TestMapObjectCreatedByMapScript(MAKEFOURCC('s', 'p', 'r', 'o')));
    T_ASSERT(!G_TestMapObjectCreatedByMapScript(MAKEFOURCC('s', 'l', 'o', 'c')));
}
#endif
