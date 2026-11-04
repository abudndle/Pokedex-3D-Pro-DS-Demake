# C356 exact Album photo resume

Scope: the existing #227 / #301 resume and Album compatibility requirements.
Opening a valid photo now checkpoints its canonical AR_0000.png-style ID,
whole-file CRC32 and byte length. Boot locates that filename in the current
descending roster, decodes read-only, and restores only matching contents.
Inserting newer photos changes the list rank but not the restored photo.
Missing, changed or invalid files return to the list with an unavailable notice.
CRC32 detects accidental changes; it is not a cryptographic authenticity check.

P3RV v7 is an optional 96-byte checkpoint: active tag at 76, reserved byte 77,
photo ID at 78, file CRC32 at 80, byte count at 84, reserved 88–91, checkpoint
CRC32 at 92. Inactive views still write v3. Existing v1–v6, Challenge v4 and
learnset v6 handling remains supported. The stream checksum adds no second read
or source-sized allocation. Album page and ID lookup share a bounded 1250-byte
namespace bitmap and one directory scan per lookup.

Regressions: `run_c356_photo_resume.sh`, `run_c356_photo_identity.sh`,
`test_c356_photo_resume_gate.py`. The initial v7 load regression failed against
the pre-change reader. Tests cover restart, torn/invalid slots, legacy detail
transitions, CRC/length mismatch, actual valid-file replacement, deletion and
roster insertion. The C268 workflow compiles a BlocksDS ROM and runs actual
melonDS restart/roster-change/replacement scenarios using synthetic PNGs only.

Status before independent CI: implemented/unverified. Physical DS/DSi behavior,
original-game asset fidelity, camera hardware and the full #301 contract remain
unverified. No original assets, private payloads or private hashes are added.
