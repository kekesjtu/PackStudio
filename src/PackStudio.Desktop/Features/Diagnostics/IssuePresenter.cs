using System.Windows.Controls;
using PackStudio.Core;

namespace PackStudio.Desktop;

public sealed class IssuePresenter
{
    readonly Workspace workspace;
    readonly ListBox list;
    readonly TextBlock summary;
    public IssuePresenter(Workspace workspace, ListBox list, TextBlock summary)
    {
        this.workspace = workspace;
        this.list = list;
        this.summary = summary;
        workspace.IssuesChanged += Refresh;
        list.SelectionChanged += (_, _) =>
        {
            if (list.SelectedItem is ValidationIssue issue) workspace.LocateIssue(issue);
        };
        Refresh();
    }

    void Refresh()
    {
        var issues = workspace.Issues;
        list.ItemsSource = issues;
        int errors = issues.Count(i => i.Severity == IssueSeverity.Error);
        summary.Text = issues.Count == 0 ? "" : $"{errors} 个错误，{issues.Count - errors} 个警告 · 点击定位";
    }
}
