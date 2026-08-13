# Environment report

- Captured (UTC): 2026-08-12T16:39:14Z
- Host: `cecelia`
- OS: `Linux-5.15.0-186-generic-x86_64-with-glibc2.35`
- Python: `3.10.12` at `/usr/bin/python3`

## CPU and memory

```text
Architecture:                            x86_64
CPU op-mode(s):                          32-bit, 64-bit
Address sizes:                           46 bits physical, 48 bits virtual
Byte Order:                              Little Endian
CPU(s):                                  80
On-line CPU(s) list:                     0-79
Vendor ID:                               GenuineIntel
Model name:                              Intel(R) Xeon(R) CPU E5-2673 v4 @ 2.30GHz
CPU family:                              6
Model:                                   79
Thread(s) per core:                      2
Core(s) per socket:                      20
Socket(s):                               2
Stepping:                                1
CPU max MHz:                             3600.0000
CPU min MHz:                             1200.0000
BogoMIPS:                                4599.99
Flags:                                   fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch cpuid_fault epb cat_l3 cdp_l3 invpcid_single pti intel_ppin ssbd ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm cqm rdt_a rdseed adx smap intel_pt xsaveopt cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln pts md_clear flush_l1d ibpb_exit_to_user
Virtualization:                          VT-x
L1d cache:                               1.3 MiB (40 instances)
L1i cache:                               1.3 MiB (40 instances)
L2 cache:                                10 MiB (40 instances)
L3 cache:                                100 MiB (2 instances)
NUMA node(s):                            2
NUMA node0 CPU(s):                       0-19,40-59
NUMA node1 CPU(s):                       20-39,60-79
Vulnerability Gather data sampling:      Not affected
Vulnerability Indirect target selection: Not affected
Vulnerability Itlb multihit:             KVM: Mitigation: VMX disabled
Vulnerability L1tf:                      Mitigation; PTE Inversion; VMX conditional cache flushes, SMT vulnerable
Vulnerability Mds:                       Mitigation; Clear CPU buffers; SMT vulnerable
Vulnerability Meltdown:                  Mitigation; PTI
Vulnerability Mmio stale data:           Mitigation; Clear CPU buffers; SMT vulnerable
Vulnerability Reg file data sampling:    Not affected
Vulnerability Retbleed:                  Not affected
Vulnerability Spec rstack overflow:      Not affected
Vulnerability Spec store bypass:         Mitigation; Speculative Store Bypass disabled via prctl and seccomp
Vulnerability Spectre v1:                Mitigation; usercopy/swapgs barriers and __user pointer sanitization
Vulnerability Spectre v2:                Mitigation; Retpolines; IBPB conditional; IBRS_FW; STIBP conditional; RSB filling; PBRSB-eIBRS Not affected; BHI Not affected
Vulnerability Srbds:                     Not affected
Vulnerability Tsa:                       Not affected
Vulnerability Tsx async abort:           Mitigation; Clear CPU buffers; SMT vulnerable
Vulnerability Vmscape:                   Mitigation; IBPB before exit to userspace
total        used        free      shared  buff/cache   available
Mem:           251Gi       6.6Gi       118Gi       165Mi       126Gi       243Gi
Swap:          8.0Gi       0.0Ki       8.0Gi
```

## GPU

```text
0, NVIDIA GeForce RTX 5090, 595.71.05, 32607 MiB, 5210 MiB, 26902 MiB, 100 %
1, NVIDIA GeForce RTX 2080 Ti, 595.71.05, 22528 MiB, 925 MiB, 21077 MiB, 100 %
2, NVIDIA GeForce RTX 2080 Ti, 595.71.05, 22528 MiB, 923 MiB, 21079 MiB, 100 %
3, NVIDIA GeForce RTX 2080 Ti, 595.71.05, 22528 MiB, 925 MiB, 21077 MiB, 100 %
4, NVIDIA GeForce RTX 2080 Ti, 595.71.05, 22528 MiB, 769 MiB, 21234 MiB, 100 %
```

No GPU was paused for this report. Utilization is a point-in-time observation.

## Disk

```text
NAME   TYPE  FSTYPE              SIZE ROTA MOUNTPOINTS       MODEL
loop0  loop  squashfs           63.9M    0 /snap/core20/2318
loop1  loop  squashfs           63.8M    0 /snap/core20/2866
loop2  loop  squashfs             74M    0 /snap/core22/2411
loop3  loop  squashfs          115.1M    0 /snap/lxd/40115
loop4  loop  squashfs          115.3M    0 /snap/lxd/40338
loop5  loop  squashfs           38.8M    0 /snap/snapd/21759
loop6  loop  squashfs           50.1M    0 /snap/snapd/27591
sda    disk  linux_raid_member 931.5G    1                   ST91000640SS
└─md0  raid5 ext4                5.5T    1 /data
sdb    disk  linux_raid_member 931.5G    1                   ST91000640SS
└─md0  raid5 ext4                5.5T    1 /data
sdc    disk  linux_raid_member 931.5G    1                   ST91000640SS
└─md0  raid5 ext4                5.5T    1 /data
sdd    disk  linux_raid_member 931.5G    1                   ST91000640SS
└─md0  raid5 ext4                5.5T    1 /data
sde    disk  linux_raid_member 931.5G    1                   ST91000640SS
└─md0  raid5 ext4                5.5T    1 /data
sdf    disk                    447.1G    0                   INTEL SSDSC2BB48
├─sdf1 part  vfat                  1G    0 /boot/efi
└─sdf2 part  ext4              446.1G    0 /
sdg    disk  linux_raid_member 931.5G    1                   ST91000640SS
└─md0  raid5 ext4                5.5T    1 /data
sdh    disk  linux_raid_member 931.5G    1                   ST91000640SS
└─md0  raid5 ext4                5.5T    1 /data
Filesystem     Type  Size  Used Avail Use% Mounted on
/dev/sdf2      ext4  439G  152G  264G  37% /
/dev/md0       ext4  5.5T  669G  4.5T  13% /data
```

Large assets go to `/data/GeoLogParser`; code and latency-sensitive small files
remain at `/root/GeoLogParser`.

## Python AI/document packages

- `torch`: not installed
- `transformers`: not installed
- `vllm`: not installed
- `paddle`: not installed
- `paddleocr`: not installed
- `onnxruntime`: not installed
- `fitz`: not installed
- `pytesseract`: not installed

These entries describe the host/project Python captured at the start of the
round. A pre-existing isolated AI runtime was subsequently verified at
`/root/venvs/ai`: Python 3.10.12, PyTorch 2.13.0+cu130, Transformers 5.14.1,
Accelerate 1.14.0, Torchvision 0.28.0, Safetensors 0.8.0, Tokenizers 0.22.2,
Pillow 12.3.0, and huggingface-hub 1.24.0. It imports
`Qwen3VLForConditionalGeneration` successfully. The exact project-facing lock
is `requirements-vlm.txt`; this runtime is not mixed into `.venv`.

## External runtimes

- `docker`: `/usr/bin/docker`; Docker version 29.1.3, build 29.1.3-0ubuntu3~22.04.2
- `tesseract`: `/usr/bin/tesseract`; tesseract 4.1.1
- `pdftotext`: `/usr/bin/pdftotext`; pdftotext version 22.02.0
- `nvcc`: `not found`; unavailable: [Errno 2] No such file or directory: 'nvcc'
- `ollama`: `not found`; unavailable: [Errno 2] No such file or directory: 'ollama'
- `llama-cli`: `not found`; unavailable: [Errno 2] No such file or directory: 'llama-cli'
- `librecad`: `/usr/bin/librecad`; LibreCAD 2.1.3 help exposes file opening and
  debug options but no advertised batch PDF/PNG export option. Offscreen GUI
  startup probes are audit-only and produced no exports.

## Locally observed model assets

- `/data/LLM` contains about 455 GB of text-LLM assets, including Qwen-family
  FP8 directories and one GGUF text LLM observed in the bounded scan.
- Numerous image/video diffusion weights and LoRAs exist under `/data`.
- No complete Chinese document OCR, layout, or document-VLM checkpoint was
  identified by the bounded scan on 2026-08-12.
- Project-selected runtime inventory is frozen in
  `configs/models/registry_v001.yaml`: Tesseract 4.1.1, RapidOCR 1.4.4 with
  ONNX Runtime 1.23.2 and three hashed OCR weights, the hash-bound B3
  positioned-text heuristic, and Qwen3-VL-4B-Instruct revision
  `ebb281ec...`. This is a bounded GeoLogParser inventory, not a claim that all
  unrelated host model assets have been licensed or audited.

## Compatibility and operational risks

1. NVIDIA driver is visible, but `nvcc` is not on the host PATH; each selected
   PyTorch/Paddle/vLLM build must be checked against its bundled CUDA runtime and
   this new GPU/driver combination.
2. The host system Python lacks the project ML stack. A project `.venv` now
   contains the lightweight test environment; use a versioned model container or
   dedicated extra for heavier runtimes and do not mutate unrelated environments.
3. All five GPUs were at 100% utilization from mining during the snapshot.
   Schedule one explicit card for inference, pause only that worker, log the
   action, and restore it after use.
4. RTX 5090 and RTX 2080 Ti have different compute generations. A single wheel/
   kernel stack may not be optimal or compatible across both; test adapters per
   hardware class.
5. `/data` is a mechanical RAID5 volume: suitable for large immutable assets,
   but page crops and random-access training shards may need an SSD staging
   cache with bounded retention.
6. Tesseract 4.1.1, `chi_sim`, and Poppler 22.02.0 were installed during the
   foundation round. Their age makes them a smoke-test baseline, not an assumed
   competitive OCR system.

## Verified project model/runtime inventory after engineering audits

Rechecked on 2026-08-12 after the baseline runs:

- Qwen3-VL-4B-Instruct revision
  `ebb281ec70b05090aa6165b016eac8ec08e71b17`, Apache-2.0, resides on the
  mechanical volume at
  `/data/GeoLogParser/models/huggingface/Qwen3-VL-4B-Instruct` (8.3 GiB).
- The isolated `/root/venvs/ai` audit runtime currently reports Transformers
  5.14.1, PyTorch 2.13.0, and Accelerate 1.14.0. The lightweight project venv
  reports RapidOCR 1.4.4 and ONNX Runtime 1.23.2. PaddleOCR and a learned layout
  model are not installed or selected; the registry records that explicitly.
  Weight SHA256 values are
  `30a01a0556622645a3cce87b655bbbbbc1f170c196099f1b666c93202c3339a9`
  and
  `046296a2a387efb43b0c997d5833c789604d168834f6e0d3064bf7bb13d002a6`;
  `config.json` SHA256 is
  `edac7703329133edfc53e46ac0081835144c99d7eebf28b71c732694d435224d`.
- The dedicated `/root/venvs/ai` runtime imports PyTorch 2.13.0+cu130,
  Transformers 5.14.1, Accelerate 1.14.0, Torchvision 0.28.0+cu130,
  Safetensors 0.8.0, Tokenizers 0.22.2, Pillow 12.3.0, and
  huggingface-hub 1.24.0. This runtime produced the indexed B2/B4/B5/B6 audits.
- RapidOCR model assets occupy about 16 MiB under
  `/data/GeoLogParser/models/rapidocr`; exact ONNX hashes are frozen in
  `configs/models/registry_v001.yaml`. The project `.venv` currently provides
  RapidOCR 1.4.4 and ONNX Runtime 1.23.2.
- GeoPackage support was added with Pyogrio 0.11.1 and Pyproj 3.7.1. PyVista
  0.48.4 and VTK 9.6.2 are now installed in the project virtual environment
  for CPU/off-screen Paper III interoperability checks. GemPy, GeoPandas,
  PaddleOCR, vLLM, Ollama, and llama.cpp remain absent from the project
  runtime. Their absence blocks optional adapters, not the
  implemented schema/constraint/evaluation/export paths.
- Current disk check: SSD `/` has about 263 GiB available; mechanical `/data`
  has about 4.5 TiB available. Large models, datasets, and robustness derivatives
  remain under `/data`; code and small random-access artifacts remain on SSD.

## GPU worker pause/restore mapping

Read-only Docker inspection on 2026-08-12 verified that each miner has restart
policy `unless-stopped` and an explicit GPU UUID:

| Physical GPU | GPU UUID | Container |
|---|---|---|
| RTX 5090 index 0 | `GPU-9858f74c-f213-32bc-b3ea-ce73cfbf3432` | `Pearl` |
| RTX 2080 Ti index 2 | `GPU-c04228ef-d18d-b4c5-0f48-a3628e8d094a` | `Pearl-2080Ti-1` |
| RTX 2080 Ti index 1 | `GPU-ce3e20b4-8629-d6a7-6654-ad58b8464b9d` | `Pearl-2080Ti-2` |
| RTX 2080 Ti index 3 | `GPU-04459f99-d29e-5495-a648-f50a50eeb86a` | `Pearl-2080Ti-3` |
| RTX 2080 Ti index 4 | `GPU-5999ff4d-d19c-3c20-ba1a-87ad5548d1ec` | `Pearl-2080Ti-4` |

The fleet is supervised by `pearl-guardian.service`; a bare `docker stop` is
therefore automatically recovered and is not a persistent maintenance pause.
The verified maintenance sequence is to send
`{"command":"miner_stop","target":"rtx5090"}` to
`/run/pearl-guardian/guardian.sock`, wait for the miner process to disappear and
the GPU to become idle, run with explicit `CUDA_VISIBLE_DEVICES`, then send
`miner_start` for the same target. Verify the operator flag, miner process,
container health, memory, and utilization. Do not kill the loop/miner process
directly. This behavior was discovered during the first VLM smoke; that run's
latency remains preserved but should not be used as the clean timing estimate.
