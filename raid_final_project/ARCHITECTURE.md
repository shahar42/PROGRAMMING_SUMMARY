# RAID 10 Storage System - High Level Architecture

## Project Overview

**Goal:** Provide tech companies a cost-effective, reliable storage solution using repurposed/old hard drives with RAID 10 implementation.

**Key Technology:** Userspace C++ RAID controller exposed as a block device via NBD (Network Block Device).

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER SPACE                               │
│                                                                  │
│  [User] ──drag/drop──> [OS File Manager]                       │
│                              ↓                                   │
│                    [Filesystem: ext4/XFS/btrfs]                 │
│                              ↓                                   │
│                  (mounted on /dev/nbd0)                         │
└──────────────────────────────────────────────────────────────────┘
                               ↓
                    (block-level I/O requests)
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│                       KERNEL SPACE                                │
│                                                                   │
│                   [NBD Kernel Module]                            │
│           (intercepts /dev/nbd0 operations)                      │
│                          ↓                                        │
│              (NBD protocol over socket)                          │
└──────────────────────────────────────────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│                    USER SPACE - YOUR SYSTEM                       │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │          NBD Server Component                          │     │
│  │  - Handles NBD protocol                                │     │
│  │  - Receives read/write requests                        │     │
│  │  - Returns responses to kernel                         │     │
│  └─────────────────┬──────────────────────────────────────┘     │
│                    ↓                                             │
│  ┌────────────────────────────────────────────────────────┐     │
│  │     RAID 10 CONTROLLER ("Master Program")             │     │
│  │                                                        │     │
│  │  - Translates logical blocks → physical locations     │     │
│  │  - Implements striping logic                          │     │
│  │  - Implements mirroring logic                         │     │
│  │  - Handles drive failures                             │     │
│  │  - Manages metadata                                   │     │
│  └─────────────────┬──────────────────────────────────────┘     │
│                    ↓                                             │
│           ┌────────┴────────┐                                    │
│           ↓                 ↓                                    │
│  ┌────────────────┐  ┌────────────────┐                        │
│  │  Mirror Set 0  │  │  Mirror Set 1  │  ...                   │
│  │                │  │                │                         │
│  │  ┌──────────┐  │  │  ┌──────────┐  │                        │
│  │  │ Drive 0  │  │  │  │ Drive 2  │  │                        │
│  │  │/dev/sda  │  │  │  │/dev/sdc  │  │                        │
│  │  └──────────┘  │  │  └──────────┘  │                        │
│  │       +        │  │       +        │                         │
│  │  ┌──────────┐  │  │  ┌──────────┐  │                        │
│  │  │ Drive 1  │  │  │  │ Drive 3  │  │                        │
│  │  │/dev/sdb  │  │  │  │/dev/sdd  │  │                        │
│  │  └──────────┘  │  │  └──────────┘  │                        │
│  └────────────────┘  └────────────────┘                        │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: User Writes a File

### Step-by-Step Flow:

1. **User Action:**
   - User drags `document.pdf` (64KB) into mounted directory
   - OS filesystem (ext4) handles file operations

2. **Filesystem → Block Layer:**
   - Filesystem translates file write into block operations
   - Example: "Write 64KB at logical offset 1048576"

3. **Kernel NBD Module:**
   - Intercepts write to `/dev/nbd0`
   - Packages request into NBD protocol message
   - Sends over Unix socket to userspace NBD server

4. **NBD Server:**
   - Receives NBD request: `{type: WRITE, offset: 1048576, length: 65536, data: [...]}`
   - Passes to RAID controller

5. **RAID 10 Controller (Master Program):**

   **Striping Logic:**
   - Assumes 32KB stripe size
   - Chunk 0 (32KB): bytes 0-32767 → Mirror Set 0
   - Chunk 1 (32KB): bytes 32768-65535 → Mirror Set 1

   **Mirroring Logic:**
   - For Mirror Set 0:
     - Write chunk 0 to `/dev/sda` at physical offset X
     - Write chunk 0 to `/dev/sdb` at physical offset X (mirror copy)
   - For Mirror Set 1:
     - Write chunk 1 to `/dev/sdc` at physical offset Y
     - Write chunk 1 to `/dev/sdd` at physical offset Y (mirror copy)

6. **Physical Drives:**
   - Each drive receives direct block writes via `pwrite()`
   - Data is now stored redundantly and striped

7. **Response Path:**
   - RAID controller confirms all writes succeeded
   - NBD server sends success response to kernel
   - Kernel completes filesystem operation
   - User sees file copy complete

---

## Component Responsibilities

### 1. NBD Server Component
**Role:** Protocol handler and kernel interface

**Responsibilities:**
- Accept NBD connections (Unix socket or TCP)
- Parse NBD protocol requests (READ, WRITE, FLUSH, TRIM, etc.)
- Validate requests
- Call RAID controller functions
- Package responses back to kernel
- Handle disconnections/errors

**Interface (conceptual):**
```cpp
class NBDServer {
    void start(const std::string& socket_path);
    void stop();

    // Callbacks from NBD library
    void onRead(uint64_t offset, uint32_t length, uint8_t* buffer);
    void onWrite(uint64_t offset, uint32_t length, const uint8_t* data);
    void onFlush();
};
```

### 2. RAID 10 Controller (Master Program)
**Role:** Core RAID logic and coordination

**Responsibilities:**
- **Striping:** Map logical offsets to physical drives/offsets
- **Mirroring:** Duplicate writes across mirror pairs
- **Read optimization:** Choose which mirror to read from (load balancing)
- **Failure detection:** Monitor drive health, handle I/O errors
- **Degraded mode:** Continue operating with failed drive
- **Rebuild:** Reconstruct mirror from surviving copy
- **Metadata management:** Track drive membership, RAID state

**Key Algorithms:**
```
Logical offset → Stripe mapping:
  stripe_num = logical_offset / stripe_size
  mirror_set = stripe_num % num_mirror_sets
  offset_in_stripe = logical_offset % stripe_size
  physical_offset = (stripe_num / num_mirror_sets) * stripe_size + offset_in_stripe

Write operation:
  For each stripe chunk:
    1. Calculate target mirror set
    2. Write to primary drive in set
    3. Write to secondary drive in set (mirror)
    4. Both must succeed or handle failure

Read operation:
  1. Calculate which mirror set holds data
  2. Choose drive (primary, or secondary if primary degraded)
  3. Read from single drive (no need to read both mirrors)
```

**Interface (conceptual):**
```cpp
class RAID10Controller {
    void initialize(const std::vector<std::string>& drive_paths);

    int read(uint64_t offset, uint32_t length, uint8_t* buffer);
    int write(uint64_t offset, uint32_t length, const uint8_t* data);
    void flush();

    void markDriveFailed(int drive_id);
    void rebuildDrive(int drive_id, const std::string& new_drive_path);

    uint64_t getTotalCapacity();
    RAIDStatus getStatus();
};
```

### 3. Drive Manager
**Role:** Low-level drive I/O and health monitoring

**Responsibilities:**
- Open/close physical drives (`/dev/sdX`)
- Direct I/O operations (read/write with proper alignment)
- SMART monitoring (detect failing drives proactively)
- Error handling and retry logic
- Performance statistics

**Interface (conceptual):**
```cpp
class DriveManager {
    bool openDrive(const std::string& path);
    void closeDrive();

    ssize_t read(uint64_t offset, uint32_t length, uint8_t* buffer);
    ssize_t write(uint64_t offset, uint32_t length, const uint8_t* data);

    bool isHealthy();
    DriveStats getStats();
};
```

### 4. Metadata Manager
**Role:** Persistent configuration and state

**Responsibilities:**
- Store RAID configuration (which drives, stripe size, etc.)
- Track drive states (healthy, degraded, failed)
- Persist rebuild progress
- Configuration file or on-disk superblocks

**Data to Persist:**
- RAID UUID
- Drive members and their roles
- Stripe configuration
- Current state (clean, degraded, rebuilding)
- Event log (drive failures, rebuilds, etc.)

---

## RAID 10 Configuration

### Topology:
- **Minimum drives:** 4 (2 mirror sets × 2 drives each)
- **Expandable:** 6, 8, 10... drives (always even number)
- **Layout:** Stripe across N/2 mirror sets

### Example with 4 drives:
```
Mirror Set 0: Drive 0 ⟷ Drive 1 (mirrors)
Mirror Set 1: Drive 2 ⟷ Drive 3 (mirrors)

Data striped: even stripes → Set 0, odd stripes → Set 1
```

### Capacity Calculation:
```
Total raw capacity = sum of all drive sizes
Usable capacity = total raw capacity / 2  (50% due to mirroring)

Example: 4 × 1TB drives = 2TB usable
```

---

## Key Design Decisions Needed

### 1. Stripe Size
**Options:** 4KB, 8KB, 16KB, 32KB, 64KB, 128KB, etc.

**Tradeoffs:**
- **Small (4-16KB):** Better for random I/O, more overhead
- **Large (64-128KB):** Better for sequential I/O, less flexible
- **Recommendation:** Start with 64KB (common default)

### 2. I/O Model
**Options:**
- Synchronous blocking I/O
- Async I/O (`libaio`, `io_uring`)
- Thread pool

**Recommendation:** Start simple (synchronous), optimize later with `io_uring`

### 3. Metadata Storage
**Options:**
- External config file (`/etc/raid10.conf`)
- Superblock on each drive (like mdadm)
- Separate metadata partition

**Recommendation:** Superblock on drives for production, config file for development

### 4. Failure Handling Strategy
**Options:**
- Immediate failover (mark degraded, continue)
- Retry with timeout
- Panic and stop (safest but least available)

**Recommendation:** Mark degraded, continue in degraded mode, alert operator

---

## Performance Characteristics

### Read Performance:
- **Best case:** 2× single drive (can read from both mirrors in parallel theoretically)
- **Typical:** ~1.5× single drive (load balancing across mirrors)
- **Random reads:** Excellent (can distribute across all drives)

### Write Performance:
- **Throughput:** ~1× single drive (must write to both mirrors)
- **Latency:** Slightly higher (wait for both mirrors)
- **Sequential writes:** Good (parallel writes to different mirror sets)

### Redundancy:
- **Tolerance:** Can lose 1 drive per mirror set (2 drives max if from different sets)
- **Risk:** Losing both drives in same mirror set = data loss

---

## Development Roadmap

### Phase 1: Core RAID Logic (No NBD)
- Implement RAID controller
- Stripe/mirror algorithms
- Direct drive I/O
- Unit tests with file-backed "drives"

### Phase 2: NBD Integration
- Integrate NBD library
- Connect RAID controller to NBD callbacks
- Test with kernel mount

### Phase 3: Reliability Features
- Drive failure detection
- Degraded mode operation
- Hot spare support
- Rebuild functionality

### Phase 4: Production Hardening
- SMART monitoring
- Logging and alerting
- Performance optimization
- Recovery tools

---

## Technology Stack (To Be Decided)

### Core Language:
- **C++17/20/23** (modern features, good performance)

### NBD Library Options:
- `libnbd` (LGPL)
- Custom implementation
- `nbd-server` codebase reference

### I/O Library:
- POSIX I/O (simple)
- `libaio` (Linux async I/O)
- `io_uring` (modern, best performance)

### Build System:
- CMake (recommended)
- Meson
- Make

### Testing:
- Google Test / Catch2
- Loop devices for testing
- Failure injection framework

---

## Success Criteria

1. **Functional:** User can mount filesystem, read/write files normally
2. **Reliable:** Survives single drive failure without data loss
3. **Performant:** Achieves expected RAID 10 performance characteristics
4. **Observable:** Clear logging, status reporting, health monitoring
5. **Recoverable:** Can rebuild failed drive from mirror

---

## Next Steps

1. **Finalize design decisions** (stripe size, I/O model, NBD library)
2. **Set up development environment** (build system, testing framework)
3. **Implement Phase 1** (core RAID logic without NBD)
4. **Integrate NBD** (Phase 2)
5. **Test and harden** (Phases 3-4)
