
from datetime import datetime
import pickle
import os
import argparse

class Task:
    """Representation of a task."""

    def __init__(self, unique_id, name, priority=1, due_date=None):
        self.created = datetime.now()
        self.completed = None
        self.deleted = False  # New attribute to mark deleted tasks
        self.name = name
        self.unique_id = unique_id
        self.priority = priority
        self.due_date = due_date

    def mark_completed(self):
        """Mark the task as completed."""
        self.completed = datetime.now()

    def mark_deleted(self):
        """Mark the task as deleted."""
        self.deleted = True



class Tasks:
    """A list of `Task` objects."""

    def __init__(self):
        self.file_path = ".todo.pickle"
        self.tasks = []
        self.load_tasks()

    def pickle_tasks(self):
        """Save the task list to a file."""
        with open(self.file_path, "wb") as f:
            pickle.dump(self.tasks, f)

    def load_tasks(self):
        """Load tasks from the `.todo.pickle` file."""
        if os.path.exists(self.file_path):
            with open(self.file_path, "rb") as f:
                self.tasks = pickle.load(f)
        else:
            self.tasks = []

    def add(self, task):
        """Add a new task."""
        self.tasks.append(task)
        self.pickle_tasks()

    def delete(self, unique_id):
        """Delete a task by unique ID."""
        self.tasks = [t for t in self.tasks if t.unique_id != unique_id]
        self.pickle_tasks()

    def list(self):
        """List all not completed tasks, excluding deleted tasks, sorted by due date and priority."""
        not_completed_tasks = [task for task in self.tasks if task.completed is None and not task.deleted]
        sorted_tasks = sorted(
            not_completed_tasks,
            key=lambda t: (t.due_date if t.due_date else datetime.min, -t.priority),
            reverse=True  # Decreasing order of due date
        )
        return sorted_tasks


    def query(self, keywords):
        """Search for tasks that contain any of the keywords in their name."""
        not_completed_tasks = [t for t in self.tasks if t.completed is None]
        return [
            t for t in not_completed_tasks if any(keyword.lower() in t.name.lower() for keyword in keywords)
        ]

    def done(self, unique_id):
        """Mark a task as completed."""
        for task in self.tasks:
            if task.unique_id == unique_id:
                task.mark_completed()
                self.pickle_tasks()
                return True
        return False

    def report(self):
        """List all tasks, including completed ones, sorted by due date and priority."""
        return sorted(self.tasks, key=lambda t: (t.due_date or datetime.max, -t.priority))
    
    def get_task_by_id(self, unique_id):
        """Retrieve a task by its unique ID."""
        for task in self.tasks:
            if task.unique_id == unique_id:
                return task
        return None


def print_tasks(tasks, show_created=False, show_completed=False, show_deleted=False):
    """Print tasks in a formatted table."""
    # Print header dynamically
    header = f"{'ID':<4}{'Age':<6}{'Due Date':<12}{'Priority':<10}{'Task':<20}"
    if show_created:
        header += f"{'Created':<30}"
    if show_completed:
        header += f"{'Completed':<30}"
    if show_deleted:
        header += f"{'Deleted':<10}"
    print(header)
    print("-" * len(header))

    # Print each task dynamically
    for task in tasks:
        # Correct Age calculation
        age_days = (datetime.now() - task.created).days
        age = f"{age_days}d" if age_days > 0 else "0d"

        due_date = task.due_date.strftime("%m/%d/%Y") if task.due_date else "-"
        row = f"{task.unique_id:<4}{age:<6}{due_date:<12}{task.priority:<10}{task.name:<20}"
        if show_created:
            created = task.created.strftime("%a %b %d %H:%M:%S %Z %Y")
            row += f"{created:<30}"
        if show_completed:
            completed = task.completed.strftime("%a %b %d %H:%M:%S %Z %Y") if task.completed else "-"
            row += f"{completed:<30}"
        if show_deleted:
            deleted_status = "Yes" if task.deleted else "No"
            row += f"{deleted_status:<10}"
        print(row)




def handle_command(args):
    tasks_manager = Tasks()

    # Add Command
    if args.add is not None:
        # Validate task name: it must not be purely numeric
        if not args.add or args.add.isdigit():
            print('There was an error in creating your task. Run "todo -h" for usage instructions.')
            return

        # Attempt to parse due date
        due_date = None
        if args.due:
            try:
                due_date = datetime.strptime(args.due, "%m/%d/%Y")
            except ValueError:
                print("Warning: Invalid due date format. Task will be added without a due date.")

        # Add task
        unique_id = len(tasks_manager.tasks) + 1
        tasks_manager.add(Task(unique_id, args.add, args.priority or 1, due_date))
        print(f"Created task {unique_id}")

    # List Command
    elif args.list:
        tasks = tasks_manager.list()
        print_tasks(tasks, show_created=False, show_completed=False)

    # Query Command
    elif args.query:
        tasks = tasks_manager.query(args.query)
        print_tasks(tasks, show_completed=False)

    # Done Command
    elif args.done:
        if tasks_manager.done(args.done):
            print(f"Completed task {args.done}")
        else:
            print(f"Error: Task with ID {args.done} not found.")

    # Delete Command
    elif args.delete:
        task = tasks_manager.get_task_by_id(args.delete)
        if task:
            task.mark_deleted()
            tasks_manager.pickle_tasks()
            print(f"Deleted task {args.delete}")
        else:
            print(f"Error: Task with ID {args.delete} not found.")

    # Report Command
    elif args.report:
        tasks = tasks_manager.tasks  # Include all tasks, even deleted ones
        print_tasks(tasks, show_created=True, show_completed=True, show_deleted=True)

    else:
        print("Error: No valid command provided. Run 'todo.py -h' for usage instructions.")


def main():
    parser = argparse.ArgumentParser(description="Task management system", allow_abbrev=False)

    # Add task flag with optional arguments
    parser.add_argument("--add", type=str, nargs="?", const="", help="Add a new task with the given name")
    parser.add_argument("--due", type=str, help="Due date (MM/DD/YYYY)")
    parser.add_argument("--priority", type=int, choices=[1, 2, 3], help="Priority level (1, 2, 3)")

    # Other commands
    parser.add_argument("--list", action="store_true", help="List all not completed tasks")
    parser.add_argument("--query", nargs="+", help="Search tasks by keyword")
    parser.add_argument("--done", type=int, help="Mark a task as completed")
    parser.add_argument("--delete", type=int, help="Delete a task by unique ID")
    parser.add_argument("--report", action="store_true", help="List all tasks (completed and incomplete)")

    # Parse arguments with fallback for unknown ones
    args, unknown_args = parser.parse_known_args()

    # Log a warning for invalid flags
    for arg in unknown_args:
        if arg.startswith("-"):
            print(f"Warning: Unknown argument '{arg}' ignored.")

    handle_command(args)



if __name__ == "__main__":
    main()