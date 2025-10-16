#hipaa_training/cli.py
from datetime import datetime 
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from .models import UserManager, DatabaseManager, ComplianceDashboard
from .training_engine import EnhancedTrainingEngine
from .security import SecurityManager


class CLI:
    """
    Command-line interface for HIPAA Training System

    FIXES APPLIED:
    - Better error handling
    - User input validation
    - Improved UX with Rich formatting
    - Secure logging using validated input
    """

    def __init__(self):
        self.console = Console()
        self.db = DatabaseManager()
        self.user_manager = UserManager()
        self.training_engine = EnhancedTrainingEngine()
        self.compliance_dashboard = ComplianceDashboard()
        self.security = SecurityManager()

    def run(self):
        """Main CLI loop"""
        self._display_welcome()

        while True:
            try:
                self._display_menu()
                choice = input("\n👉 Enter your choice (1-5): ").strip()

                # ✅ Validate and sanitize choice before logging or using
                try:
                    choice = self.security.validate_input(
                        choice,
                        field_name="menu_choice",
                        max_length=10,
                        pattern=r"^[1-5]$"
                    )
                except ValueError:
                    self.console.print("[red]❌ Invalid input detected. Please enter 1-5.[/red]")
                    continue

                self.security.log_action(0, "MENU_ACCESS", f"Selected option: {choice}")

                if choice == "1":
                    self._create_user()
                elif choice == "2":
                    self._start_training()
                elif choice == "3":
                    self._complete_checklist()
                elif choice == "4":
                    self._generate_report()
                elif choice == "5":
                    self.console.print(
                        "\n[green]👋 Exiting HIPAA Training System. Goodbye![/green]\n"
                    )
                    break
                else:
                    self.console.print("[red]❌ Invalid choice. Please enter 1-5.[/red]")

            except KeyboardInterrupt:
                self.console.print("\n\n[yellow]⚠ Interrupted by user[/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]❌ Error: {str(e)}[/red]")
                self.security.log_action(0, "ERROR", f"CLI Error: {str(e)}")

    def _display_welcome(self):
        """Display welcome message with system info"""
        self.console.print(
            Panel.fit(
                "[bold cyan]Welcome to HIPAA Training System V3.0.1[/bold cyan]\n"
                "Enterprise-grade compliance training for pharmacies\n\n"
                f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}\n"
                f"⚡ Status: Production Ready",
                title="🏥 HIPAA Training",
                border_style="cyan",
            )
        )

    def _display_menu(self):
        """Display main menu with better formatting"""
        table = Table(show_header=False, border_style="blue", padding=(0, 2))
        table.add_column("Option", style="cyan bold")
        table.add_column("Description", style="white")

        table.add_row("1", "👤 Create New User")
        table.add_row("2", "📚 Start Training Session")
        table.add_row("3", "✅ Complete Compliance Checklist")
        table.add_row("4", "📊 Generate Compliance Report")
        table.add_row("5", "🚪 Exit System")

        self.console.print("\n")
        self.console.print(table)

    def _create_user(self):
        """Create a new user with validation"""
        self.console.print("\n[bold cyan]👤 Create New User[/bold cyan]")
        self.console.print("─" * 50)

        try:
            username = input("Username: ").strip()
            if not username:
                self.console.print("[red]❌ Username cannot be empty[/red]")
                return

            full_name = input("Full Name: ").strip()
            if not full_name:
                self.console.print("[red]❌ Full name cannot be empty[/red]")
                return

            self.console.print("\nAvailable roles:")
            self.console.print("  • admin   - Full system access")
            self.console.print("  • staff   - Complete training")
            self.console.print("  • auditor - View reports only")

            role = input("\nRole (admin/staff/auditor): ").strip().lower()

            user_id = self.user_manager.create_user(username, full_name, role)

            self.console.print(
                Panel(
                    f"[green]✅ User created successfully![/green]\n\n"
                    f"User ID: {user_id}\n"
                    f"Username: {username}\n"
                    f"Role: {role}",
                    border_style="green",
