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
    bool expanded;
    bool? decidedForErrors;
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

    // 面板展开状态跟随当前是否存在错误：出现错误自动展开，只有重叠警告时默认收起；
    // 点击切换的展开状态保持到错误状态改变或问题清空为止。
    void Refresh()
    {
        var issues = workspace.Issues;
        list.ItemsSource = issues;
        bool errors = issues.Any(i => i.Severity == IssueSeverity.Error);
        if (issues.Count == 0) decidedForErrors = null;
        else if (decidedForErrors != errors)
        {
            SetExpanded(errors);
            decidedForErrors = errors;
        }
        Summarize();
    }

    void Summarize()
    {
        var issues = workspace.Issues;
        int errors = issues.Count(i => i.Severity == IssueSeverity.Error);
        summary.Text = issues.Count == 0 ? "" : $"{errors} 个错误，{issues.Count - errors} 个警告 · {(expanded ? "点击定位" : "点击展开")}";
    }
}
