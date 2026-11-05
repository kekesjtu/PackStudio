namespace PackStudio.Core;

internal sealed class ModelGenerationException(string code, string message) : ArgumentException(message)
{
    public string Code { get; } = code;
}
