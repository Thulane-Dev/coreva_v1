from django.apps import apps
from django.db.models import Q
from datetime import date
from django.utils import timezone
from collections import defaultdict
from django.db.models import Prefetch


# Models Import
IssueModel = apps.get_model(
    "issues", "IssueModel")
IssueCommentModel = apps.get_model(
    "issues", "IssueCommentModel")
ProjectContractor = apps.get_model(
    "projects", "ProjectContractor")
ProjectModel = apps.get_model(
    "projects", "ProjectModel")



# ==================================================
# Project Open Issues
# ==================================================
def get_project_issues_workspace(
        project,
        contractor=None,
        show_project_details=None,
):  
    # Open Issues
    open_issues_list = []
    closed_issues_list = []
    comments_issues_list = []
    overdue_issues_count = 0

    if show_project_details == False:
        open_issues = IssueModel.objects.filter(
            Q(project=project) & Q(status='open') & Q(type='issue') & Q(assigned_contractor =contractor)).prefetch_related(
            Prefetch(
                "issue",
                queryset=IssueCommentModel.objects.filter(
                    is_read=False).order_by("-created_at"),
                to_attr="unread_comments"
            )
        ).order_by("-created_at")
    elif show_project_details == True:
         open_issues = IssueModel.objects.filter(
            Q(project=project) & Q(type='issue') & Q(assigned_contractor =contractor)).prefetch_related(
            Prefetch(
                "issue",
                queryset=IssueCommentModel.objects.filter(
                    is_read=False).order_by("-created_at"),
                to_attr="unread_comments"
            )
        ).order_by("-created_at")

    for issue in open_issues:
        comment_count = 0

        # DAYS LEFT CHECK
        days_left = (
            issue.due_date - date.today()).days

        if days_left < 0:
            issue_text = f"Due {abs(days_left)} days ago"
            overdue_issues_count += 1
            is_overdue = True

        elif days_left == 0:
            issue_text = "Due today"
            is_overdue = False

        elif days_left == 1:
            issue_text = "Due tomorrow"
            is_overdue = False

        else:
            issue_text = f"Due in {days_left} days"
            is_overdue = False

        # comment check
        for comment in issue.unread_comments:
            comment_count += 1

        if comment_count > 0:
            comments_issues_list.append(issue)

        # Check Issue Status 
        if issue.status == 'open':
            open_issues_list.append({
                "issue": issue,
                "status": issue.priority,
                "issue_text": issue_text,
                "is_overdue": is_overdue,
                "comment_count": comment_count,
            })
        else:
             closed_issues_list.append({
                "issue": issue,
                "status": issue.priority,
                "issue_text": issue_text,
                "is_overdue": is_overdue,
                "comment_count": comment_count,
            })

    return {
        "open_issues_list": open_issues_list,
        "overdue_issues_count" : overdue_issues_count,
        "comments_issues_list": comments_issues_list,
    }



# ==================================================
# Project Open Tasks
# ==================================================
def get_project_tasks_workspace(
        project,
        contractor=None,
        show_project_details=None,
):
    # Open Issues
    open_task_list = []
    closed_task_list = []
    comments_tasks_list = []
    overdue_tasks_count = 0

    if show_project_details == False:
        open_tasks = IssueModel.objects.filter(
            Q(project=project) & Q(status='open') & Q(type='task') & Q(assigned_contractor =contractor)).prefetch_related(
            Prefetch(
                "issue",
                queryset=IssueCommentModel.objects.filter(
                    is_read=False).order_by("-created_at"),
                to_attr="unread_comments"
            )
        ).order_by("-created_at")
    elif show_project_details == True:
         open_tasks = IssueModel.objects.filter(
            Q(project=project) & Q(type='task') & Q(assigned_contractor =contractor)).prefetch_related(
            Prefetch(
                "issue",
                queryset=IssueCommentModel.objects.filter(
                    is_read=False).order_by("-created_at"),
                to_attr="unread_comments"
            )
        ).order_by("-created_at") 

    for task in open_tasks:
        comment_count = 0

        # check days left
        days_left = (
            task.due_date - date.today()).days

        if days_left < 0:
            task_text = f"Due {abs(days_left)} days ago"
            is_overdue = True
            overdue_tasks_count += 1

        elif days_left == 0:
            task_text = "Due today"
            is_overdue = False

        elif days_left == 1:
            task_text = "Due tomorrow"
            is_overdue = False

        else:
            task_text = f"Due in {days_left} days"
            is_overdue = False

        # comment check
        for comment in task.unread_comments:
            comment_count += 1

        if comment_count > 0:
            comments_tasks_list.append(task)

        # Check status 
        if task.status == 'open':
            open_task_list.append({
                "task": task,
                "status": task.priority,
                "task_text": task_text,
                "is_overdue": is_overdue,
                "comment_count": comment_count,
            })
        else:
             closed_task_list.append({
                "task": task,
                "status": task.priority,
                "task_text": task_text,
                "is_overdue": is_overdue,
                "comment_count": comment_count,
            })


    return {
        "open_task_list": open_task_list,
        "overdue_tasks_count" : overdue_tasks_count,
        "comments_tasks_list": comments_tasks_list,
    }



# ==================================================
# Project Data - One Project data
# ==================================================
def get_workspace_project_data(
        project,
        contractor=None,
        show_project_details=None,
):

    # ======================= Issues Functions ===========================
    issues_data = get_project_issues_workspace(project=project,contractor=contractor, show_project_details = show_project_details)
    open_issues = issues_data['open_issues_list']
    issue_comments = issues_data['comments_issues_list']
    total_issues_comments = len(issue_comments)

    # ======================== Tasks Functions ==========================
    tasks_data = get_project_tasks_workspace(project=project,contractor=contractor, show_project_details = show_project_details)
    open_tasks = tasks_data['open_task_list']
    task_comments = tasks_data['comments_tasks_list']
    total_tasks_comments = len(task_comments)

    total_comments = total_issues_comments + total_tasks_comments
    

    return {
        # ISSUES 
        "open_issues" : open_issues,
        "issues_count": len(open_issues),
        "overdue_issues_count" : issues_data['overdue_issues_count'],
        "comments_issues_list" : issue_comments,
        "total_issues_comments" : total_issues_comments,
        

        # TASKS 
        "open_tasks" : open_tasks,
        "tasks_count": len(open_tasks),
        "overdue_tasks_count" : tasks_data['overdue_tasks_count'],
        "comments_tasks_list" : task_comments,
        "total_tasks_comments" : total_tasks_comments,

        # TOTAL COMMENTS 
        "total_comments" : total_comments,
        "total_work_count" : len(open_issues) + len(open_tasks),
        "total_overdue_count" : issues_data['overdue_issues_count'] + tasks_data['overdue_tasks_count']
    }




# ==================================================
# Main Dashboard Projects Workspace data
# ==================================================
def get_workspace_data(
        contractor
):
    
    # projects = ProjectModel.objects.filter(
    #     projects__contractor=contractor
    # ).order_by('created_at')

    projects_list = []

    contractor_projects = ProjectContractor.objects.filter(contractor=contractor).order_by('created_at')
    show_project_details = False

    for contractor in contractor_projects:
        project_data = get_workspace_project_data(project=contractor.project,contractor=contractor,show_project_details=show_project_details)

        # ================ Issues ================
        open_issues_count = project_data['issues_count']
        overdue_issues_count = project_data['overdue_issues_count']
        total_issues_comments = project_data['total_issues_comments']


        # ================ Issues ================
        open_tasks_count = project_data['tasks_count']
        overdue_tasks_count = project_data['overdue_tasks_count']
        total_tasks_comments = project_data['total_tasks_comments']



        status_count = 0 

        # Issues status Check 
        if open_issues_count > 0:
            status_count += 1

        if overdue_issues_count > 0:
                    status_count += 1

        if total_issues_comments > 0:
                    status_count += 1 

        # Tasks status Check 
        if open_tasks_count > 0:
            status_count += 1

        if overdue_tasks_count > 0:
                    status_count += 1

        if total_tasks_comments > 0:
                    status_count += 1 

        # Project If needs Attention status  
        if status_count > 0:
             status = True
        else:
             status = False

        # Create project Object
        project_object = {
            "project": contractor.project,
            "status" : status,
            "portal_uuid": contractor.uuid,

            "issues_count": open_issues_count,
            "overdue_issues_count": overdue_issues_count,
            "comments_issues_list": total_issues_comments,

            "tasks_count": open_tasks_count,
            "overdue_tasks_count": overdue_tasks_count,
            "comments_tasks_list": total_tasks_comments,

        }

        projects_list.append(project_object)


    return {
        "contractor": contractor,
        "projects_list" : projects_list,
    }