from setuptools import setup

with open('README.md') as f:
    long_description = f.read()

setup(
    name='jb',
    version='1.0',
    url='https://github.com/jetbridge/backend-core',
    license='ABRMS',
    author='JetBridge',
    author_email='mischa@jetbridge.com',
    description='Common reusable code for python projects.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    # py_modules=['jb'],
    # if you would be using a package instead use packages instead
    # of py_modules:
    packages=['jb'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask',
        'boto3',
        'sqlalchemy',
        'requests',
    ],
)
