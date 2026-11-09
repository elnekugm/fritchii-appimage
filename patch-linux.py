#!/usr/bin/env python3
"""Minimal Linux fixes for building Fritchii v5.5 from source.

Run from the Fritchii source tree. Four defects in the tag only appear on a
GCC/X11 Linux build (the first two are the same fixes documented by
Gusdevr/fritchii-linux-build):

1. host_memory.cpp: g_committed_bytes is declared in the _WIN32-only anonymous
   namespace, but HostMemory::CommitAllBut() logs it unconditionally.
2. vk_pipeline_cache.cpp: Xlib.h (pulled in by the Vulkan Xlib headers) defines
   `Status` as `int`, which breaks PipelineCacheMergeResult::Status.
3. vk_graphics_pipeline.cpp: NoteDrawReuseProbeFrame() is used from
   vk_rasterizer.cpp with a local declaration only; GCC -Werror=missing-declarations
   rejects the definition.
4. path_util.h/.cpp: GetExeDirectory() is declared and defined only under
   _WIN32, yet video_core/nx2_precompile.cpp calls it from every platform.
   Provide a POSIX implementation (Linux: /proc/self/exe).
"""
from pathlib import Path

# 1. host_memory.cpp
p = Path("src/common/host_memory.cpp")
s = p.read_text()
old = (
    '    LOG_INFO(HW_Memory, "EDEN_NX2_SEC_RESERVE: {} MiB of guest memory committed (the kernel\'s own)",\n'
    '             g_committed_bytes.load(std::memory_order_relaxed) >> 20);\n'
)
new = "#ifdef _WIN32\n" + old + "#endif\n"
assert old in s, "host_memory.cpp: anchor not found"
p.write_text(s.replace(old, new, 1))
print("patched host_memory.cpp")

# 2. vk_pipeline_cache.cpp
p = Path("src/video_core/renderer_vulkan/vk_pipeline_cache.cpp")
s = p.read_text()
anchor = "namespace Vulkan {"
assert anchor in s, "vk_pipeline_cache.cpp: anchor not found"
if "#undef Status" not in s:
    s = s.replace(anchor, "#undef Status  // Xlib.h defines Status as int\n\n" + anchor, 1)
    p.write_text(s)
    print("patched vk_pipeline_cache.cpp")

# 3. vk_graphics_pipeline.cpp
p = Path("src/video_core/renderer_vulkan/vk_graphics_pipeline.cpp")
s = p.read_text()
anchor = "void NoteDrawReuseProbeFrame() {"
assert anchor in s, "vk_graphics_pipeline.cpp: anchor not found"
if "void NoteDrawReuseProbeFrame();" not in s:
    s = s.replace(anchor, "void NoteDrawReuseProbeFrame();\n\n" + anchor, 1)
    p.write_text(s)
    print("patched vk_graphics_pipeline.cpp")

# 4a. path_util.h: declare GetExeDirectory() on non-Windows too.
p = Path("src/common/fs/path_util.h")
s = p.read_text()
anchor = "/**\n * Gets the path of the directory specified by the #HOME environment variable."
assert anchor in s, "path_util.h: anchor not found"
if s.count("[[nodiscard]] std::filesystem::path GetExeDirectory();") != 2:
    declaration = (
        "/**\n"
        " * Gets the path of the directory containing the executable of the current process.\n"
        " *\n"
        " * @returns The path of the directory containing the executable of the current process.\n"
        " */\n"
        "[[nodiscard]] std::filesystem::path GetExeDirectory();\n\n"
    )
    s = s.replace(anchor, declaration + anchor, 1)
    p.write_text(s)
    print("patched path_util.h")

# 4b. path_util.cpp: implement it in the non-Windows branch.
p = Path("src/common/fs/path_util.cpp")
s = p.read_text()
anchor = "fs::path GetHomeDirectory() {"
assert anchor in s, "path_util.cpp: anchor not found"
if "/proc/self/exe" not in s:
    implementation = (
        "fs::path GetExeDirectory() {\n"
        "    std::error_code error;\n"
        "#ifdef __linux__\n"
        "    if (auto exe = fs::read_symlink(\"/proc/self/exe\", error); !error) {\n"
        "        return exe.parent_path();\n"
        "    }\n"
        "#endif\n"
        "    return fs::current_path(error);\n"
        "}\n\n"
    )
    s = s.replace(anchor, implementation + anchor, 1)
    p.write_text(s)
    print("patched path_util.cpp")

print("all patches applied")
