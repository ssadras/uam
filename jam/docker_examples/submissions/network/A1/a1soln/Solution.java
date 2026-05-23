package a1soln;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.Socket;

/**
 * Malicious submission: tries to make outbound network calls.
 *
 * Verifies that {@code docker_network = 'none'} prevents student code
 * from exfiltrating data or contacting external hosts. With the
 * sandbox active the {@code Socket} construction below should fail
 * almost immediately; the test driver records the failure under the
 * 'errors' bucket and the test_runner itself stays healthy.
 */
public final class Solution {

    private Solution() {
    }

    private static void tryConnect() throws IOException {
        Socket socket = new Socket();
        try {
            socket.connect(new InetSocketAddress("example.com", 80), 2000);
        } finally {
            socket.close();
        }
    }

    public static int safeSum(int[] nums) {
        try {
            tryConnect();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        return 0;
    }

    public static double safeAverage(int[] nums) {
        try {
            tryConnect();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        return 0.0;
    }
}
