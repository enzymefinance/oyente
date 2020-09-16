from setuptools import find_packages, setup

setup(
    name='oyente',
    version='0.2.7',
    author='Loi Luu',
    # author_email='',
    url='https://github.com/melonport/oyente',
    description='An analysis tool for smart contracts',
    long_description=open('README.md').read(),
    license='GPL',
    keywords='ethereum smart contracts',
    classifiers=[
        'Environment :: Console',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ],
    packages=find_packages(),
    package_data={
        'oyente': ['state.json'],
    },
    entry_points={
        'console_scripts': [
            'oyente = oyente.oyente:main',
        ]
    },
    install_requires=[
        'requests',
        'web3',
        'z3-solver',
        'crytic-compile',
    ]
)
