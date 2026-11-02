using PackStudio.Core;

string root = Path.GetFullPath(args.FirstOrDefault() ?? ".");
var tests = new TestSuite(root, args.Skip(1).ToHashSet(StringComparer.OrdinalIgnoreCase));
CatalogChecks.Run(tests);
ParameterChecks.Run(tests);
LayoutChecks.Run(tests);
MaterialChecks.Run(tests);
ProjectChecks.Run(tests);
return tests.Finish();
