# ABOUTME: CLI command to seed the widget library with standard clinical trial widgets
# ABOUTME: Run with: python -m app.cli.seed_widgets_command

import click
import logging
from sqlmodel import Session
from app.core.db import engine
from app.db.seed_widgets import seed_widgets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--force",
    is_flag=True,
    help="Force update existing widgets"
)
@click.option(
    "--email",
    default="admin@example.com",
    help="Email of the user to use for seeding"
)
def seed_widgets_command(force: bool, email: str):
    """Seed the database with standard clinical trial widgets"""
    from app.models.user import User
    
    db = Session(engine)
    
    try:
        logger.info("Starting widget seeding process...")
        
        # Get user for seeding
        user = db.query(User).filter(User.email == email).first()
        if not user:
            click.echo(click.style(f"❌ User with email '{email}' not found. Please create a user first.", fg="red"))
            raise click.Abort()
        
        if force:
            logger.info("Force mode enabled - will update existing widgets")
        
        seed_widgets(db, user.id)
        
        click.echo(click.style("✅ Widget seeding completed successfully!", fg="green"))
        
    except Exception as e:
        logger.error(f"Error during widget seeding: {str(e)}")
        click.echo(click.style(f"❌ Widget seeding failed: {str(e)}", fg="red"))
        raise click.Abort()
    
    finally:
        db.close()


if __name__ == "__main__":
    seed_widgets_command()