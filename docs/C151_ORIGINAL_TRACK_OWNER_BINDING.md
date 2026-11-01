# C151 — Bind original C5 track owners to native P3SK nodes

C148 recovered original C5 skeleton indices and original parent links, C149 added the real native P3SK reader, and C150 added exact original node-name and ancestry lookup. C151 adds a **native C binding gate** that can associate a source animation owner with a loaded original node **only if both its original node index and exact source node name agree**.

The gate rejects missing rigs, invalid indices, duplicates, wrong-case names, null strings and model-switch stale pointers. A two-pass check ensures it never publishes partial output: rejected track lists leave every bounded output slot marked `0xffff`. No heuristic mapping, bone retargeting, resampling, synthetic action names or substitute animations are introduced. A host-compiled C regression uses normal and suffix-interned **synthetic** P3SK data, including corrupted/mismatched owners.

**Not complete:** This proves a safe native binding API, not that all 25,956 private C5 source tracks have been linked to private P3SK records in an authorized asset-integrated ROM. C147/C148 SHA-bound private audit and original action/clip boundaries must still be verified, along with exact local matrix conventions, skin weights, and animation timing before original skeletal playback can be enabled. The current development ROM remains asset-free. Issue #122's Right/B emulator interaction failure remains unresolved.

Private original C5/P3SK files, textures, converted models and Nintendo ROMs remain outside public GitHub.
