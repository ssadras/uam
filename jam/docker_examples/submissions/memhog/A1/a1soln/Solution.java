package a1soln;

import java.util.ArrayList;
import java.util.List;

/**
 * Malicious submission: allocates more memory than the container has.
 *
 * Verifies that {@code docker_memory} kills the JVM (via OOM-killer or
 * a Java {@code OutOfMemoryError}) before the host's free memory is
 * touched.
 *
 * The allocation is sized at ~1 GiB worth of bytes -- well above the
 * default {@code docker_memory = '512m'}. Outside the sandbox this
 * will simply cause the host JVM to balloon; do not run without
 * {@code docker_enabled = true}.
 */
public final class Solution {

    private Solution() {
    }

    private static void eatMemory() {
        List<byte[]> chunks = new ArrayList<>();
        for (int i = 0; i < 64; i++) {              // 64 * 16 MiB = 1 GiB
            chunks.add(new byte[16 * 1024 * 1024]); // 16 MiB
        }
    }

    public static int safeSum(int[] nums) {
        eatMemory();
        return 0;
    }

    public static double safeAverage(int[] nums) {
        eatMemory();
        return 0.0;
    }
}
