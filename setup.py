from distutils.core import setup
setup(
  name = 'line_sizing',         # How you named your package folder (MyLib)
  package = 'line_sizing',
  package_data={'line_sizing':['pr_2.xlsx']},
  include_package_data=True,
  version = '1.1',      # Start with a small number and increase it with every change you make
  license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'Line sizing calculations',   # Give a short description about your library
  author = 'Kevin Dorma',                   # Type in your name
  author_email = 'kevin@kevindorma.ca',      # Type in your E-Mail
  url = 'https://github.com/Carbonn14/Line_sizing',   # Provide either the link to your github or to your website
  download_url = 'https://github.com/Carbonn14/Line_sizing/dist/v1.1.tar.gz',    # I explain this later on
  keywords = ['Line sizing', 'engineering', 'safety'],   # Keywords that define your package best
  install_requires=[            # I get to this in a second
          'numpy',
          'pandas',
          'scipy',
      ],
)