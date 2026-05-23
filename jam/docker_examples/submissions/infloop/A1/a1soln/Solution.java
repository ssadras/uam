package a1soln;

/**
 * Malicious submission: safeSum spins forever.
 *
 * Verifies that {@code docker_timeout} and the host-level subprocess
 * timeout kill the container even when student code refuses to exit.
 *
 * WARNING: do NOT run the test_runner against this submission without
 * {@code docker_enabled = true}. Outside the sandbox this will hang
 * the host JVM until the host timeout fires.
 */
public final class Solution {

    private Solution() {
    }

    public static int safeSum(int[] nums) {
        long spin = 0;
        while (true) {
            spin++; // prevent the JIT from optimising the loop away
        }
    }

    public static double safeAverage(int[] nums) {
        return safeSum(nums);
    }
}
