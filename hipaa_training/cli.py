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
                )
            )

        except ValueError as e:
            self.console.print(f"[red]❌ Error: {str(e)}[/red]")
        except Exception as e:
            self.console.print(f"[red]❌ Unexpected error: {str(e)}[/red]")

    def _start_training(self):
        """Start training session for a user"""
        self.console.print("\n[bold cyan]📚 Start Training Session[/bold cyan]")
        self.console.print("─" * 50)

        user_id_input = input("Enter user ID: ").strip()

        # Validate user ID
        if not user_id_input.isdigit():
            self.console.print("[red]❌ Invalid user ID. Must be a number.[/red]")
            return

        user_id = int(user_id_input)

        if not self.user_manager.user_exists(user_id):
            self.console.print(f"[red]❌ User ID {user_id} not found.[/red]")
            return

        # Display user info
        user = self.user_manager.get_user(user_id)
        if user:
            self.console.print(
                f"\n[green]✓ User found: {user['full_name']} ({user['role']})[/green]\n"
            )

        try:
            # Go through all lessons
            lessons = list(self.training_engine.content.lessons.keys())
            self.console.print(
                f"[cyan]Starting training with {len(lessons)} lessons...[/cyan]\n"
            )

            for idx, lesson in enumerate(lessons, 1):
                self.console.print(f"\n[bold]Lesson {idx}/{len(lessons)}[/bold]")
                self.training_engine.display_lesson(user_id, lesson)

                # Mini quiz for comprehension
                if not self.training_engine._mini_quiz(
                    self.training_engine.content.lessons[lesson]
                ):
                    self.console.print(
                        "[red]❌ Failed comprehension quiz. Please review the lesson.[/red]"
                    )
                    retry = input("Retry lesson? (yes/no): ").strip().lower()
                    if retry in ["yes", "y"]:
                        self.training_engine.display_lesson(user_id, lesson)
                        if not self.training_engine._mini_quiz(
                            self.training_engine.content.lessons[lesson]
                        ):
                            self.console.print(
                                "[red]❌ Failed again. Moving to next lesson.[/red]"
                            )
                    continue

                self.db.save_progress(user_id, lesson, None, None)

            # Final adaptive quiz
            self.console.print("\n" + "=" * 60)
            self.console.print("[bold cyan]📝 Final Assessment Quiz[/bold cyan]")
            self.console.print("=" * 60)

            score = self.training_engine.adaptive_quiz(user_id)

            # Check if passed
            from .models import Config

            if score >= Config.PASS_THRESHOLD:
                certificate_id = self.db.issue_certificate(user_id, score)
                self.console.print(
                    Panel(
                        f"[bold green]🎉 Congratulations![/bold green]\n\n"
                        f"Training completed successfully!\n"
                        f"Final Score: {score:.1f}%\n"
                        f"Certificate ID: {certificate_id}\n\n"
                        f"Your certificate is valid for {Config.TRAINING_EXPIRY_DAYS} days",
                        border_style="green",
                        title="✅ Training Complete",
                    )
                )
            else:
                self.console.print(
                    Panel(
                        f"[bold red]Training Not Completed[/bold red]\n\n"
                        f"Final Score: {score:.1f}%\n"
                        f"Required: {Config.PASS_THRESHOLD}%\n\n"
                        f"Please retake the training to earn your certificate.",
                        border_style="red",
                        title="❌ Below Passing Score",
                    )
                )

        except Exception as e:
            self.console.print(f"[red]❌ Training error: {str(e)}[/red]")
            self.security.log_action(user_id, "TRAINING_ERROR", str(e))

    def _complete_checklist(self):
        """Complete compliance checklist for a user"""
        self.console.print("\n[bold cyan]✅ Compliance Checklist[/bold cyan]")
        self.console.print("─" * 50)

        user_id_input = input("Enter user ID: ").strip()

        if not user_id_input.isdigit():
            self.console.print("[red]❌ Invalid user ID. Must be a number.[/red]")
            return

        user_id = int(user_id_input)

        if not self.user_manager.user_exists(user_id):
            self.console.print(f"[red]❌ User ID {user_id} not found.[/red]")
            return

        try:
            self.training_engine.complete_enhanced_checklist(user_id)
            self.db.save_sensitive_progress(
                user_id, self.training_engine.checklist, None
            )
            self.console.print("\n[green]✅ Checklist saved successfully![/green]")
        except Exception as e:
            self.console.print(f"[red]❌ Checklist error: {str(e)}[/red]")

    def _generate_report(self):
        """Generate compliance report"""
        self.console.print("\n[bold cyan]📊 Generate Compliance Report[/bold cyan]")
        self.console.print("─" * 50)

        self.console.print("\nAvailable formats:")
        self.console.print("  • csv  - Spreadsheet format")
        self.console.print("  • json - Structured data format")

        format_type = input("\nEnter report format (csv/json): ").strip().lower()

        if format_type not in ["csv", "json"]:
            self.console.print("[red]❌ Invalid format. Use 'csv' or 'json'.[/red]")
            return

        try:
            filename = self.compliance_dashboard.generate_enterprise_report(format_type)
            self.console.print(
                Panel(
                    f"[green]✅ Report generated successfully![/green]\n\n"
                    f"📁 File: {filename}\n"
                    f"📊 Format: {format_type.upper()}",
                    border_style="green",
                )
            )
        except Exception as e:
            self.console.print(f"[red]❌ Report generation failed: {str(e)}[/red]")

# ...end of file...
