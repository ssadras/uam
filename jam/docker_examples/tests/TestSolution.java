/*
 * Self-contained UAM test driver for the JAM Docker sandbox example.
 *
 * This class is staged into each student's submission directory by the
 * preamble command, then compiled and run inside the sandbox
 * container. It runs a fixed spec against ``a1soln.Solution`` and
 * writes a UAM-compatible ``result.json``.
 *
 * It depends on the JDK only -- no JUnit, no external jars -- so the
 * example works with a vanilla ``openjdk:11-slim`` image.
 *
 * Spec under test
 * ---------------
 *   Solution.safeSum(int[] nums)      -> int. Sum of nums.
 *   Solution.safeAverage(int[] nums)  -> double. Mean of nums; 0.0 if empty.
 *
 * Both methods are expected to be total (no exceptions on valid input).
 */

import java.io.IOException;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

import a1soln.Solution;

public final class TestSolution {

    private interface Probe {
        Object run() throws Throwable;
    }

    private static final class Case {
        final String id;
        final Probe probe;
        final Object expected;

        Case(String id, Probe probe, Object expected) {
            this.id = id;
            this.probe = probe;
            this.expected = expected;
        }
    }

    private static List<Case> spec() {
        List<Case> cases = new ArrayList<>();
        cases.add(new Case("test_sum_empty",
                () -> Solution.safeSum(new int[] {}), 0));
        cases.add(new Case("test_sum_one",
                () -> Solution.safeSum(new int[] {42}), 42));
        cases.add(new Case("test_sum_many",
                () -> Solution.safeSum(new int[] {1, 2, 3, 4}), 10));
        cases.add(new Case("test_sum_negatives",
                () -> Solution.safeSum(new int[] {-1, 1, -2, 2}), 0));
        cases.add(new Case("test_avg_empty",
                () -> Solution.safeAverage(new int[] {}), 0.0));
        cases.add(new Case("test_avg_one",
                () -> Solution.safeAverage(new int[] {10}), 10.0));
        cases.add(new Case("test_avg_many",
                () -> Solution.safeAverage(new int[] {2, 4, 6}), 4.0));
        return cases;
    }

    public static void main(String[] args) throws IOException {
        List<Case> spec = spec();
        StringBuilder passes = new StringBuilder();
        StringBuilder failures = new StringBuilder();
        StringBuilder errors = new StringBuilder();
        StringBuilder allTests = new StringBuilder();
        boolean anyBad = false;

        for (int i = 0; i < spec.size(); i++) {
            Case c = spec.get(i);
            if (allTests.length() > 0) allTests.append(", ");
            allTests.append(jsonString(c.id));

            try {
                Object actual = c.probe.run();
                if (equalsBoxed(actual, c.expected)) {
                    if (passes.length() > 0) passes.append(", ");
                    passes.append(jsonString(c.id)).append(": ")
                          .append(jsonString(c.id));
                } else {
                    anyBad = true;
                    if (failures.length() > 0) failures.append(", ");
                    failures.append(jsonString(c.id)).append(": ")
                            .append(failureRecord(c.id,
                                    "expected " + repr(c.expected)
                                  + ", got " + repr(actual)));
                }
            } catch (Throwable t) {
                anyBad = true;
                if (errors.length() > 0) errors.append(", ");
                errors.append(jsonString(c.id)).append(": ")
                      .append(errorRecord(c.id, t));
            }
        }

        StringBuilder testCase = new StringBuilder("{");
        boolean wroteBucket = false;
        if (passes.length() > 0) {
            testCase.append("\"passes\": {").append(passes).append('}');
            wroteBucket = true;
        }
        if (failures.length() > 0) {
            if (wroteBucket) testCase.append(", ");
            testCase.append("\"failures\": {").append(failures).append('}');
            wroteBucket = true;
        }
        if (errors.length() > 0) {
            if (wroteBucket) testCase.append(", ");
            testCase.append("\"errors\": {").append(errors).append('}');
        }
        testCase.append('}');

        String json = "{\n"
                + "  \"students\": [],\n"
                + "  \"results\": {\"docker_examples.SolutionTests\": "
                + testCase + "},\n"
                + "  \"date\": \"N/A\",\n"
                + "  \"assignment\": \"N/A\",\n"
                + "  \"tests\": [" + allTests + "]\n"
                + "}\n";

        String target = System.getenv().getOrDefault("UAM_RESULT_JSON",
                                                     "result.json");
        Files.write(Paths.get(target), json.getBytes(StandardCharsets.UTF_8));

        if (anyBad) {
            System.exit(1);
        }
    }

    private static boolean equalsBoxed(Object actual, Object expected) {
        if (actual == null || expected == null) return actual == expected;
        if (actual instanceof Number && expected instanceof Number) {
            return ((Number) actual).doubleValue()
                    == ((Number) expected).doubleValue();
        }
        return actual.equals(expected);
    }

    private static String repr(Object o) {
        if (o == null) return "null";
        return o.toString();
    }

    private static String failureRecord(String id, String message) {
        return "{\"description\": " + jsonString(id)
             + ", \"message\": " + jsonString(message)
             + ", \"details\": \"\"}";
    }

    private static String errorRecord(String id, Throwable t) {
        StringBuilder details = new StringBuilder();
        details.append(t.getClass().getName());
        if (t.getMessage() != null) {
            details.append(": ").append(t.getMessage());
        }
        for (StackTraceElement el : t.getStackTrace()) {
            details.append("\n  at ").append(el);
        }
        return "{\"description\": " + jsonString(id)
             + ", \"message\": " + jsonString(
                    t.getClass().getSimpleName()
                    + (t.getMessage() != null ? ": " + t.getMessage() : ""))
             + ", \"details\": " + jsonString(details.toString()) + "}";
    }

    private static String jsonString(String s) {
        StringBuilder out = new StringBuilder(s.length() + 2);
        out.append('"');
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '"':  out.append("\\\""); break;
                case '\\': out.append("\\\\"); break;
                case '\n': out.append("\\n"); break;
                case '\r': out.append("\\r"); break;
                case '\t': out.append("\\t"); break;
                default:
                    if (c < 0x20) {
                        out.append(String.format("\\u%04x", (int) c));
                    } else {
                        out.append(c);
                    }
            }
        }
        out.append('"');
        return out.toString();
    }
}
