# C150 — Native exact skeleton node-name binding and ancestry

This milestone extends the **actual native C** P3SK loader merged in C149. The source-backed private P3SK v1 format already contains original C5 node names, parent indices and raw matrix bytes. C150 exposes exact, case-sensitive source node-name lookup and bounded parent-chain traversal for later original C5 animation track association.

- `p3dOriginalSkeletonFindNode` returns an original node index only for an exact name. It never guesses case, prefixes, suffixes or substitute bone names.
- `p3dOriginalSkeletonIsAncestor` verifies strict ancestry through the source parent indices, with a node-count bound and fail-closed behavior if the loaded record memory is damaged.
- Existing CRC, source string termination, parent-index ordering, duplicate-name rejection and model-ID checks remain enforced by the original C149 loader.
- Synthetic host C/Python tests cover normal and source suffix-interned names, invalid/overlong strings, wrong-case names, ancestry, self-reference corruption, duplicate source names, bad parent, bad CRC and clear/reset behavior.

**What is not claimed:** This does not infer or implement original skin weights, vertex-to-bone assignments, action/clip selection, frame rate, interpolation, matrix conventions, 3DS shaders or original skeletal animation rendering. Private original C5 and converted P3SK binaries remain outside public GitHub. Final native ROM/DeSmuME CI is an **asset-free development** smoke test, not private original-asset proof.

Next acceptance gate: privately validate C147 original track owner name/index pairs against C148 P3SK records and only then design a CRC/SHA-bound clip/pose transport. Original action selection and mesh skinning still require source evidence. The unrelated #122 DeSmuME Right/B input regression remains open until verified.
