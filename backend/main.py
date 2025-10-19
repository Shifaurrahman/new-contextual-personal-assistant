#!/usr/bin/env python3
"""
Main entry point for the Contextual Personal Assistant
"""

import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from config import Config
from src.models import init_db, db_manager
from src.agents import IngestionAgent, ThinkingAgent
from src.services import CardService, EnvelopeService, ContextService


console = Console()





def display_menu():
    """Display main menu"""
    console.print("\n[bold yellow]Main Menu:[/bold yellow]")
    console.print("  1. Add a new note")
    console.print("  2. View all cards")
    console.print("  3. View envelopes")
    console.print("  4. Run thinking agent")
    console.print("  5. View suggestions")
    console.print("  6. View context summary")
    console.print("  7. Search cards")
    console.print("  8. Exit")
    console.print()


def add_note():
    """Add a new note"""
    console.print("\n[bold green]Add New Note[/bold green]")
    console.print("Enter your note (or 'back' to return):")
    
    note = input("📝 Note: ").strip()
    
    if note.lower() == 'back' or not note:
        return
    
    with db_manager.get_session() as db:
        agent = IngestionAgent(db)
        result = agent.process_note(note)
        
        console.print(f"\n✅ [bold green]Card created successfully![/bold green]")
        console.print(f"   Type: {result['card']['card_type']}")
        console.print(f"   Priority: {result['card']['priority']}")
        if result['envelope']:
            console.print(f"   Envelope: {result['envelope']['name']}")


def view_cards():
    """View all cards"""
    with db_manager.get_session() as db:
        card_service = CardService(db)
        cards = card_service.get_all_cards()
        
        if not cards:
            console.print("\n[yellow]No cards found.[/yellow]")
            return
        
        table = Table(title=f"\n📋 All Cards ({len(cards)} total)")
        table.add_column("ID", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Description", style="white")
        table.add_column("Priority", style="yellow")
        table.add_column("Date", style="green")
        table.add_column("Status", style="blue")
        
        for card in cards[:20]:  # Show first 20
            date_str = card.date.strftime('%Y-%m-%d') if card.date else "N/A"
            description = card.description[:50] + "..." if len(card.description) > 50 else card.description
            
            table.add_row(
                str(card.id),
                card.card_type,
                description,
                card.priority,
                date_str,
                card.status
            )
        
        console.print(table)


def view_envelopes():
    """View all envelopes"""
    with db_manager.get_session() as db:
        envelope_service = EnvelopeService(db)
        envelopes = envelope_service.get_all_envelopes()
        
        if not envelopes:
            console.print("\n[yellow]No envelopes found.[/yellow]")
            return
        
        table = Table(title=f"\n📁 All Envelopes ({len(envelopes)} total)")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Type", style="yellow")
        table.add_column("Cards", style="green")
        table.add_column("Keywords", style="blue")
        
        for envelope in envelopes:
            keywords = ", ".join(envelope.keywords[:3]) if envelope.keywords else "N/A"
            
            table.add_row(
                str(envelope.id),
                envelope.name,
                envelope.envelope_type or "N/A",
                str(len(envelope.cards)),
                keywords
            )
        
        console.print(table)


def run_thinking_agent():
    """Run the thinking agent"""
    console.print("\n[bold blue]🤔 Running Thinking Agent...[/bold blue]")
    
    with db_manager.get_session() as db:
        thinking_agent = ThinkingAgent(db)
        suggestions = thinking_agent.analyze_and_suggest()
        
        if not suggestions:
            console.print("\n[yellow]No suggestions generated.[/yellow]")
            return
        
        console.print(f"\n[bold green]✅ Generated {len(suggestions)} suggestions![/bold green]")


def view_suggestions():
    """View pending suggestions"""
    with db_manager.get_session() as db:
        thinking_agent = ThinkingAgent(db)
        suggestions = thinking_agent.get_pending_suggestions()
        
        if not suggestions:
            console.print("\n[yellow]No pending suggestions.[/yellow]")
            return
        
        table = Table(title=f"\n💡 Pending Suggestions ({len(suggestions)} total)")
        table.add_column("ID", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Title", style="white")
        table.add_column("Priority", style="yellow")
        
        for suggestion in suggestions:
            table.add_row(
                str(suggestion.id),
                suggestion.output_type,
                suggestion.title,
                suggestion.priority
            )
        
        console.print(table)
        
        # Show details of first suggestion
        if suggestions:
            first_suggestion = suggestions[0]
            console.print(f"\n[bold]Latest Suggestion:[/bold]")
            console.print(Panel(first_suggestion.description, title=first_suggestion.title))


def view_context_summary():
    """View context summary"""
    with db_manager.get_session() as db:
        context_service = ContextService(db)
        summary = context_service.get_context_summary()
        
        console.print("\n[bold cyan]📊 Context Summary[/bold cyan]")
        console.print(f"  Total contexts: {summary['total_contexts']}")
        console.print(f"  Active projects: {summary['active_projects']}")
        console.print(f"  Key people: {summary['key_people']}")
        
        if summary['by_type']:
            console.print("\n  By type:")
            for ctx_type, count in summary['by_type'].items():
                console.print(f"    • {ctx_type}: {count}")


def search_cards():
    """Search cards"""
    console.print("\n[bold green]Search Cards[/bold green]")
    query = input("🔍 Search query: ").strip()
    
    if not query:
        return
    
    with db_manager.get_session() as db:
        card_service = CardService(db)
        results = card_service.search_cards(query)
        
        if not results:
            console.print(f"\n[yellow]No cards found matching '{query}'.[/yellow]")
            return
        
        console.print(f"\n[bold]Found {len(results)} cards:[/bold]")
        for card in results[:10]:
            console.print(f"  • [{card.card_type}] {card.description}")


def demo_mode():
    """Run demo with sample notes"""
    console.print("\n[bold cyan]🎬 Running Demo Mode[/bold cyan]\n")
    
    sample_notes = [
        "Call Sarah about the Q3 budget next Monday",
        "Idea: new logo should be blue and green",
        "Remember to pick up milk on the way home",
        "Send proposal to marketing team by Friday urgent",
        "Meeting with John tomorrow at 3pm about project X",
        "Brainstorm ideas for customer retention strategy",
        "Review quarterly reports this week"
    ]
    
    with db_manager.get_session() as db:
        agent = IngestionAgent(db)
        
        console.print("[bold]Processing sample notes...[/bold]\n")
        for i, note in enumerate(sample_notes, 1):
            console.print(f"[cyan]{i}/{len(sample_notes)}[/cyan] Processing: {note}")
            try:
                agent.process_note(note)
                console.print("[green]✓[/green] Success\n")
            except Exception as e:
                console.print(f"[red]✗[/red] Error: {e}\n")
    
    console.print("[bold green]✅ Demo completed![/bold green]")


def main():
    """Main application loop"""
    try:
        # Validate configuration
        Config.validate()
        
        # Initialize database
        init_db()
        

        
        # Check if this is first run
        with db_manager.get_session() as db:
            card_service = CardService(db)
            existing_cards = card_service.get_all_cards()
            
            if len(existing_cards) == 0:
                console.print("\n[yellow]👋 Welcome! It looks like this is your first time.[/yellow]")
                console.print("[yellow]Would you like to run a demo with sample notes? (y/n)[/yellow]")
                
                choice = input("Choice: ").strip().lower()
                if choice == 'y':
                    demo_mode()
        
        # Main loop
        while True:
            display_menu()
            choice = input("Select an option (1-8): ").strip()
            
            if choice == '1':
                add_note()
            elif choice == '2':
                view_cards()
            elif choice == '3':
                view_envelopes()
            elif choice == '4':
                run_thinking_agent()
            elif choice == '5':
                view_suggestions()
            elif choice == '6':
                view_context_summary()
            elif choice == '7':
                search_cards()
            elif choice == '8':
                console.print("\n[bold cyan]👋 Goodbye![/bold cyan]\n")
                sys.exit(0)
            else:
                console.print("\n[red]Invalid option. Please try again.[/red]")
            
            input("\nPress Enter to continue...")
    
    except KeyboardInterrupt:
        console.print("\n\n[bold cyan]👋 Goodbye![/bold cyan]\n")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]\n")
        sys.exit(1)


if __name__ == "__main__":
    main()