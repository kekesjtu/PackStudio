using PackStudio.Core;

sealed class TestSuite(string root, HashSet<string> suites)
{
    public string Root { get; } = root;
    public PackageCatalog Catalog { get; } = new(Path.Combine(root, "runtime_data"));
    public ModelBuilder Builder => new(Catalog);
    int passed, failed;

    public void Case(string suite, string name, Action run)
    {
        if (suites.Count > 0 && !suites.Contains(suite)) return;
        try { run(); passed++; }
        catch (Exception error) { failed++; Console.WriteLine($"FAIL {suite}/{name}: {error.Message}"); }
    }

    public int Finish()
    {
        Console.WriteLine($"{passed} passed, {failed} failed");
        return failed == 0 && passed > 0 ? 0 : 1;
    }

    public static void Assert(bool condition, string message)
    {
        if (!condition) throw new Exception(message);
    }

    public static void Near(double actual, double expected, string message)
        => Assert(double.IsFinite(actual) && Math.Abs(actual - expected) <= 1e-8 * Math.Max(1, Math.Abs(expected)), $"{message}: {actual} != {expected}");

    public static void Reject(Action run)
    {
        try { run(); }
        catch (ArgumentException) { return; }
        throw new Exception("invalid input was accepted");
    }
}
