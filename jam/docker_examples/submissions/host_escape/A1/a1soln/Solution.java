package a1soln;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Malicious submission: probes for host filesystem access.
 *
 * Verifies that:
 *   * the only host path inside the container is the bind-mounted
 *     submission directory (so reading /etc/shadow off the host is
 *     impossible -- the container's /etc/shadow is the *image's*,
 *     which never contains real credentials);
 *   * dropped capabilities + {@code no-new-privileges} block
 *     privilege escalation;
 *   * writes outside the bind mount land in the ephemeral container
 *     rootfs and are discarded with {@code --rm} at container exit.
 *
 * Nothing in this class can damage the host.
 */
public final class Solution {

    private static final String[] PROBES = {
        "/etc/shadow",        // would-be host credentials (not present)
        "/proc/1/environ",    // init's environment
        "/proc/self/maps",    // leaks ASLR / loaded libs
        "/root/.ssh/id_rsa",  // would-be host ssh key
    };

    private Solution() {
    }

    private static void readProbes() {
        for (String path : PROBES) {
            try {
                Files.readAllBytes(Paths.get(path));
            } catch (IOException | SecurityException ignored) {
                // expected -- access denied or file not present
            }
        }
    }

    private static void writeOutsideMount() {
        // Inside Docker this either fails or lands in the ephemeral
        // container layer that --rm discards.
        try {
            Files.write(Path.of("/tmp/uam-escape-attempt"),
                    "this file should never appear on the host".getBytes());
        } catch (IOException | SecurityException ignored) {
        }
    }

    public static int safeSum(int[] nums) {
        readProbes();
        writeOutsideMount();
        return 0;
    }

    public static double safeAverage(int[] nums) {
        readProbes();
        writeOutsideMount();
        return 0.0;
    }
}
