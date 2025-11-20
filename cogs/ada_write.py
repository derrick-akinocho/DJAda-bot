import discord
from discord.ext import commands
from discord import app_commands

# --------- Vérification rôle ---------
def has_adawrite_role():
    async def predicate(interaction: discord.Interaction):
        required_role_id = 1374667434799136861
        return any(r.id == required_role_id for r in interaction.user.roles)
    return app_commands.check(predicate)

class AdaWrite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="adawrite", description="Send a message in the channel where you use the command.")
    @has_adawrite_role()
    @app_commands.describe(text="The message you want the bot to send")
    async def adawrite(self, interaction: discord.Interaction, text: str):

        await interaction.response.send_message(".", ephemeral=True)
        await interaction.delete_original_response()
        # Envoie le message dans le salon où la commande a été utilisée
        await interaction.channel.send(text)

    @adawrite.error
    async def adawrite_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("🚫 You don’t have permission to use this command.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdaWrite(bot))
