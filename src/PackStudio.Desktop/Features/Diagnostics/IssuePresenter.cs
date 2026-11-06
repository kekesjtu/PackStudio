using System.Windows;
using System.Windows.Controls;
using PackStudio.Core;

namespace PackStudio.Desktop;

public sealed class IssuePresenter
{
    readonly Workspace workspace;
    readonly ListBox list;
    readonly TextBlock summary;
    readonly TextBlock chevron;
    bool expanded = true;
    bool hadIssues;
    public IssuePresenter(Workspace workspace, ListBox list, TextBlock summary, TextBlock chevron)
    {
        this.workspace = workspace;
        this.list = list;
        this.summary = summary;
        this.chevron = chevron;
        workspace.IssuesChanged += Refresh;
        list.SelectionChanged += (_, _) =>
        {
            if (list.SelectedItem is ValidationIssue issue) workspace.LocateIssue(issue);
        };
        SetExpanded(true);
        Refresh();
    }

    // 收起时只保留一行汇总，问题列表完全隐藏；点击汇总行切换。
    public void Toggle() => SetExpanded(!expanded);

    void SetExpanded(bool value)
    {
        expanded = value;
        list.Visibility = value ? Visibility.Visible : Visibility.Collapsed;
        chevron.Text = value ? "\uE70E" : "\uE70D";
        Summarize();
    }

    void Refresh()
    {
        var issues = workspace.Issues;
        list.ItemsSource = issues;
        if (issues.Count > 0 && !hadIssues)
            SetExpanded(true);
        hadIssues = issues.Count > 0;
        Summarize();
    }

    void Summarize()
    {
        var issues = workspace.Issues;
        int errors = issues.Count(i => i.Severity == IssueSeverity.Error);
        summary.Text = issues.Count == 0 ? "" : $"{errors} 个错误，{issues.Count - errors} 个警告 · {(expanded ? "点击定位" : "点击展开")}";
    }
}
