#!/usr/bin/env python3
"""Minimal Linux fixes for building Fritchii v5.5 from source.

Run from the Fritchii source tree. Three defects in the tag only appear on a GCC/X11
Linux build (same fixes documented by Gusdevr/fritchii-linux-build):

1. host_memory.cpp: g_committed_bytes is declared in the _WIN32-only anonymous
   namespace, but HostMemory::CommitAllBut() logs it unconditionally.
2. vk_pipeline_cache.cpp: Xlib.h (pulled in by the Vulkan Xlib headers) defines
   `Status` as `int`, which breaks PipelineCacheMergeResult::Status.
3. vk_graphics_pipeline.cpp: NoteDrawReuseProbeFrame() is used from
   vk_rasterizer.cpp with a local declaration only; GCC -Werror=missing-declarations
   rejects the definition.
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

print("all patches applied")
