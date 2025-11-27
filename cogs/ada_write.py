import discord
from discord.ext import commands
from discord import app_commands

# --------- Vérification rôle (serveur uniquement) ---------
def has_adawrite_role():
    async def predicate(interaction: discord.Interaction):
        # Si c'est un DM, autoriser par défaut
        if isinstance(interaction.channel, discord.DMChannel):
            return True
        required_role_id = 1374667434799136861
        return any(r.id == required_role_id for r in interaction.user.roles)
    return app_commands.check(predicate)

class AdaWrite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Sync les commandes au démarrage du bot
        self.bot.loop.create_task(self.sync_commands())

    async def sync_commands(self):
        await self.bot.wait_until_ready()
        try:
            await self.bot.tree.sync()
            print("✅ AdaWrite commands synced")
        except Exception as e:
            print(f"❌ Failed to sync AdaWrite commands: {e}")

    @app_commands.command(name="adawrite", description="Send a message in the channel or thread where you use the command.")
    @has_adawrite_role()
    @app_commands.describe(text="The message you want the bot to send")
    async def adawrite(self, interaction: discord.Interaction, text: str):
        
        await interaction.response.send_message(".", ephemeral=True)
        await interaction.delete_original_response()

        if isinstance(interaction.channel, discord.TextChannel) or isinstance(interaction.channel, discord.Thread):
            await interaction.channel.send(text)
        else:
            # DM → essayer d'envoyer dans le thread public ModMail
            thread = getattr(self.bot.threads, "get_thread", lambda *_: None)()
            if thread:
                await thread.send(text)

    @adawrite.error
    async def adawrite_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("<:Emoji_Shrug_Street_Sovereign:1441146941172875385> You don’t have permission.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ An error occurred: {error}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdaWrite(bot))
