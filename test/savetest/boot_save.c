// Headless save-load test harness (issue #11).
//
// Boots a ROM in libmgba with a .sav, presses A until the game reaches the
// overworld via CONTINUE, keeps it running for a while to catch crashes, then
// dumps the loaded save blocks so check_save.py can compare them against the
// save's expected values.
//
// Usage: boot_save <rom.gba> <rom.sym> <save.sav> <out_dir>
//
// Exit codes: 0 reached the overworld and stayed there, 1 failed, 2 usage or
// setup error. The save file is copied before loading, so the original is
// never modified.

#include <mgba/core/core.h>
#include <mgba/core/interface.h>
#include <mgba/core/log.h>
#include <mgba-util/vfs.h>

#include <fcntl.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define GBA_KEY_A 0

// Frame budgets (the GBA runs ~60 frames per second).
#define MAX_FRAMES_TO_OVERWORLD (60 * 90)
#define STABLE_FRAMES (60 * 10)

// Sizes of the save structs, pinned to vanilla (include/global.h).
#define SAVEBLOCK1_SIZE 0x3D88
#define SAVEBLOCK2_SIZE 0xF2C

struct Symbols {
    uint32_t gMain;
    uint32_t CB2_Overworld;
    uint32_t gSaveFileStatus;
    uint32_t gSaveBlock1Ptr;
    uint32_t gSaveBlock2Ptr;
};

static int LoadSymbols(const char *path, struct Symbols *syms)
{
    FILE *f = fopen(path, "r");
    char line[512];
    int found = 0;

    if (!f) {
        perror(path);
        return 0;
    }
    memset(syms, 0, sizeof(*syms));
    while (fgets(line, sizeof(line), f)) {
        unsigned addr;
        char scope[8], size[16], name[256];
        if (sscanf(line, "%x %7s %15s %255s", &addr, scope, size, name) != 4)
            continue;
#define SYM(x) if (!strcmp(name, #x) && !syms->x) { syms->x = addr; found++; }
        SYM(gMain) SYM(CB2_Overworld) SYM(gSaveFileStatus) SYM(gSaveBlock1Ptr) SYM(gSaveBlock2Ptr)
#undef SYM
    }
    fclose(f);
    if (found != 5) {
        fprintf(stderr, "Missing symbols in %s (found %d of 5)\n", path, found);
        return 0;
    }
    return 1;
}

static int CopyFile(const char *from, const char *to)
{
    FILE *in = fopen(from, "rb"), *out;
    char buf[8192];
    size_t n;

    if (!in) {
        perror(from);
        return 0;
    }
    out = fopen(to, "wb");
    if (!out) {
        perror(to);
        fclose(in);
        return 0;
    }
    while ((n = fread(buf, 1, sizeof(buf), in)) > 0)
        fwrite(buf, 1, n, out);
    fclose(in);
    fclose(out);
    return 1;
}

static void DumpMemory(struct mCore *core, uint32_t addr, uint32_t size, const char *path)
{
    FILE *f = fopen(path, "wb");
    uint32_t i;

    if (!f) {
        perror(path);
        return;
    }
    for (i = 0; i < size; i++)
        fputc(core->busRead8(core, addr + i), f);
    fclose(f);
}

static void WriteScreenshot(const color_t *buf, unsigned w, unsigned h, const char *path)
{
    FILE *f = fopen(path, "wb");
    unsigned i;

    if (!f)
        return;
    fprintf(f, "P6\n%u %u\n255\n", w, h);
    for (i = 0; i < w * h; i++) {
        color_t c = buf[i];
#ifdef COLOR_16_BIT
        uint8_t r = (c & 0x1F) << 3, g = ((c >> 5) & 0x1F) << 3, b = ((c >> 10) & 0x1F) << 3;
#else
        uint8_t r = c & 0xFF, g = (c >> 8) & 0xFF, b = (c >> 16) & 0xFF;
#endif
        fputc(r, f);
        fputc(g, f);
        fputc(b, f);
    }
    fclose(f);
}

static void QuietLog(struct mLogger *logger, int category, enum mLogLevel level, const char *format, va_list args)
{
    (void)logger;
    (void)category;
    if (level & (mLOG_FATAL | mLOG_ERROR)) {
        vfprintf(stderr, format, args);
        fputc('\n', stderr);
    }
}

int main(int argc, char **argv)
{
    struct Symbols syms;
    struct mCore *core;
    struct VFile *saveFile;
    color_t *videoBuffer;
    unsigned width, height;
    char path[1024];
    int frame, reachedAt = -1, stableFrames = 0;
    uint32_t callback2 = 0;
    int ok;
    FILE *result;

    if (argc != 5) {
        fprintf(stderr, "Usage: %s <rom.gba> <rom.sym> <save.sav> <out_dir>\n", argv[0]);
        return 2;
    }
    static struct mLogger logger = { .log = QuietLog };
    mLogSetDefaultLogger(&logger);

    if (!LoadSymbols(argv[2], &syms))
        return 2;

    snprintf(path, sizeof(path), "%s/working.sav", argv[4]);
    if (!CopyFile(argv[3], path))
        return 2;

    core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) {
        fprintf(stderr, "Could not create an mGBA core for %s\n", argv[1]);
        return 2;
    }
    mCoreInitConfig(core, NULL);
    core->desiredVideoDimensions(core, &width, &height);
    videoBuffer = calloc((size_t)width * height, BYTES_PER_PIXEL);
    core->setVideoBuffer(core, videoBuffer, width);

    if (!mCoreLoadFile(core, argv[1])) {
        fprintf(stderr, "Could not load ROM %s\n", argv[1]);
        return 2;
    }
    saveFile = VFileOpen(path, O_RDWR);
    if (!saveFile || !core->loadSave(core, saveFile)) {
        fprintf(stderr, "Could not load save %s\n", path);
        return 2;
    }
    core->reset(core);

    // Press A for 2 frames every 20 frames. That skips the intro, passes the
    // title screen and picks CONTINUE, the first main menu option. If the save
    // doesn't load, CONTINUE isn't offered and the overworld is never reached.
    for (frame = 0; frame < MAX_FRAMES_TO_OVERWORLD + STABLE_FRAMES; frame++) {
        int pressA = reachedAt < 0 && frame > 60 && frame % 20 < 2;

        core->setKeys(core, pressA ? (1 << GBA_KEY_A) : 0);
        core->runFrame(core);
        // Function pointers are Thumb addresses, so drop the low bit.
        callback2 = core->busRead32(core, syms.gMain + 4) & ~1u;

        if (reachedAt < 0) {
            if (callback2 == syms.CB2_Overworld)
                reachedAt = frame;
            else if (frame >= MAX_FRAMES_TO_OVERWORLD)
                break;
        } else if (callback2 == syms.CB2_Overworld) {
            if (++stableFrames >= STABLE_FRAMES)
                break;
        } else {
            break; // Left the overworld while idle: crash or unexpected state.
        }
    }
    core->setKeys(core, 0);

    ok = reachedAt >= 0 && stableFrames >= STABLE_FRAMES;

    snprintf(path, sizeof(path), "%s/screenshot.ppm", argv[4]);
    WriteScreenshot(videoBuffer, width, height, path);

    snprintf(path, sizeof(path), "%s/result.txt", argv[4]);
    result = fopen(path, "w");
    if (result) {
        fprintf(result, "save_status=%u\n", core->busRead16(core, syms.gSaveFileStatus));
        fprintf(result, "reached_overworld=%d\n", reachedAt >= 0);
        fprintf(result, "frames_to_overworld=%d\n", reachedAt);
        fprintf(result, "stable_frames=%d\n", stableFrames);
        fprintf(result, "final_callback2=0x%08x\n", callback2);
        fclose(result);
    }

    if (reachedAt >= 0) {
        snprintf(path, sizeof(path), "%s/saveblock1.bin", argv[4]);
        DumpMemory(core, core->busRead32(core, syms.gSaveBlock1Ptr), SAVEBLOCK1_SIZE, path);
        snprintf(path, sizeof(path), "%s/saveblock2.bin", argv[4]);
        DumpMemory(core, core->busRead32(core, syms.gSaveBlock2Ptr), SAVEBLOCK2_SIZE, path);
    }

    printf("save_status=%u reached_overworld=%d frames_to_overworld=%d stable_frames=%d\n",
           core->busRead16(core, syms.gSaveFileStatus), reachedAt >= 0, reachedAt, stableFrames);

    core->deinit(core);
    free(videoBuffer);
    return ok ? 0 : 1;
}
