import disnake
from disnake.ext import commands

# Defines the StringSelect that contains animals that your users can choose from
class AnimalDropdown(disnake.ui.StringSelect):
    def __init__(self):
        # Define the options that will be displayed inside the dropdown.
        # You may not have more than 25 options.
        # There is a `value` keyword that is being omitted, which is useful if
        # you wish to display a label to the user, but handle a different value
        # here within the code, like an index number or database id.
        options = [
            disnake.SelectOption(label="Dog", description="Dogs are your favorite type of animal"),
            disnake.SelectOption(label="Cat", description="Cats are your favorite type of animal"),
            disnake.SelectOption(
                label="Snake", description="Snakes are your favorite type of animal"
            ),
            disnake.SelectOption(
                label="Gerbil", description="Gerbils are your favorite type of animal"
            ),
        ]

        # We will include a placeholder that will be shown until an option has been selected.
        # The min and max values indicate the minimum and maximum number of options to be selected -
        # in this example we will only allow one option to be selected.
        super().__init__(
            placeholder="Choose an animal",
            min_values=1,
            max_values=1,
            options=options,
        )

    # This callback is called each time a user has selected an option
    async def callback(self, inter: disnake.MessageInteraction):
        # Use the interaction object to respond to the interaction.
        # `self` refers to this StringSelect object, and the `values`
        # attribute contains a list of the user's selected options.
        # We only want the first (and in this case, only) one.
        await inter.response.send_message(f"Your favorite type of animal is: {self.values[0]}")


class DropDownView(disnake.ui.View):
    def __init__(self):
        # You would pass a new `timeout=` if you wish to alter it, but
        # we will leave it empty for this example so that it uses the default 180s.
        super().__init__()

        # Now let's add the `StringSelect` object we created above to this view
        self.add_item(AnimalDropdown())


class AnimalsCommand(commands.Cog):
    """This will be for a ping command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command()
    async def ddd(self, inter: disnake.ApplicationCommandInteraction):
        """Sends a message with our dropdown containing the animals"""

        # Create the view with our dropdown object
        view = DropDownView()

        # Respond to the interaction with a message and our view
        await inter.response.send_message("What is your favorite type of animal?", view=view)

def setup(bot: commands.Bot):
    bot.add_cog(AnimalsCommand(bot))