# vern

vern is a command-line interface to OpenAI's ChatGPT that supports predefined [system
roles](#system-roles), such as [recipe generator](#recipe-generator), [generate code](#code-generator),
[code commentor](#code-commentor) and [modern translator](#modern-translator), [sessions](#using-sessions), an
[interactive prompt](#interactive-prompt) interface, can read files via stdin, and will pretty-print
in markdown.

In the examples it generates Latex for a recipe given ingredients on hand, generates 
bash snippets, comments Bitcoin's pow.cpp, and translates the prolgue of Canterbury Tales.

vern is named vern in honor of Jim Varney's character Ernest P. Worrell.

Know what I mean, vern?

### Prerequisites
- Python 3.7 or newer
- pip (Python package manager)

### Quickstart
1. Clone the repository:
   ```bash
   git clone https://github.com/rpgrimm/vern.git
   ```
2. Navigate to the project source directory:
   ```bash
   cd vern
   ```
3. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Export OPENAI_API_KEY
   ```bash
   export OPENAI_API_KEY='YOUR_API_KEY'
   ```
6. Run vern_server.py
   ```bash
   ./vern/vern_server.py -i
   ```
7. In separate terminal navigate to source and activate virtual env, put vern in PATH, and test vern
    ```bash
   source venv/bin/activate
   export PATH=$PATH:$PWD/vern/
   vern what is up
   ```
   You should see something like:
```
Hello! Not much, just here to help you with any tech-related questions or anything else you might need. How can I assist you today?
```

### Interactive prompt
1.  Try vern -i for an interactive prompt:
```
vern -i
vern> give me an interesting quote from mark twain
Certainly! Here's an interesting quote from Mark Twain: "The secret of getting
ahead is getting started." This quote emphasizes the importance of taking the
first step towards achieving your goals.
vern> another
Of course! Here's another thought-provoking quote from Mark Twain: "Whenever
you find yourself on the side of the majority, it is time to pause and
reflect." This quote encourages critical thinking and the importance of
questioning popular opinion.
vern> one from eleanor roosevelt
Certainly! Here's an inspiring quote from Eleanor Roosevelt: "The future belongs to those who believe in the beauty of their dreams." This quote highlights the
power of belief and vision in shaping one's future.
vern>
```

### Using sessions

1. Start new session with name 'world-historian' and role 'be a fun learned world history buff...'
   ```
   vern --new-s world-historian be a fun learned world history buff and explain things in an engaging and humorous way
   ```
2. Use session 'world-historian' and ask about ancient egypt
   ```
   vern --use-s world-historian give me an interesting fact involing ancient egypt customs
   ```
   You should see something like:
```
One interesting fact about ancient Egyptian customs is their elaborate burial practices, particularly the mummification process. The
ancient Egyptians believed in an afterlife, and they thought that preserving the body was essential for the deceased to live on in  
the next world.                                                                                                                     

Mummification involved removing internal organs, which were then stored in canopic jars, and treating the body with natron (a       
natural salt) to dehydrate it. The body was then wrapped in linen and adorned with amulets and jewelry, as these items were believed
to provide protection and assistance in the afterlife.                                                                              

This practice reflects their deep spiritual beliefs and the importance they placed on the journey after death, showcasing a complex 
understanding of life, death, and the divine.  
```
3. Use session 'world-historian' and ask for another
   ```
   vern --use-s world-historian give me another
   ```
Since it has persistence with a session id, you'll get another:
```
Another fascinating aspect of ancient Egyptian customs is the significance of the "Weighing of the Heart" ceremony, which was a     
crucial part of their beliefs about the afterlife. According to ancient Egyptian mythology, after a person died, their heart was    
weighed against the feather of Ma'at, the goddess of truth and justice.                                                             

During this ceremony, Anubis, the god of the afterlife, would place the deceased's heart on one side of a scale and the feather on  
the other. If the heart was lighter than the feather, it indicated that the person had lived a virtuous life and was deemed worthy  
to enter the afterlife, known as the Field of Reeds. However, if the heart was heavier, it was devoured by Ammit, a fearsome        
creature that was part crocodile, lion, and hippopotamus, resulting in the soul facing eternal oblivion.                            

This custom highlights the ancient Egyptians' emphasis on morality, truth, and the consequences of one's actions in life, reflecting
their complex spiritual beliefs and societal values.
```
4.  Use vern --list-s to see sessions
```
vern --list-s
session-1700s you speak like you are from the 1700s
session-test-s You are a highly knowledgeable and tech-savvy assistant, specializing ...
session-world-historian You are a highly knowledgeable and tech-savvy assistant, specializing ...
```
5.  Use vern --rm-s to remove a session
```
vern --rm-s test-s
```

### System Roles
1.  Use --list-sys to list predefined system roles, defined in [systems.json](https://github.com/rpgrimm/vern/blob/rgrimm/deploy/vern/systems.json)
   ```
vern --list-sys
Available systems:

  - recipe-generator:
You are a LaTeX generator that formats recipes into well-structured LaTeX documents. Given a recipe title, a list of ingredients, and step-by-step instructions, output only valid LaTeX code with no explanations or comments. Do not include any markdown or Latex code blocks.  Ensure the document uses `\documentclass{article}`, properly formatted sections, a clear ingredient list, and a numbered steps section for instructions.

  - modern-translator:
You are a language modernization assistant. Your job is to translate old English text into modern, natural English while preserving meaning and tone. Avoid archaic words, restructure sentences for clarity, and ensure readability for a contemporary audience. Always return only the translated text, without explanations or formatting.

  - code-generator:
You are a code generation assistant. Always respond with raw code and no explanations, formatting, or extraneous text. Do not include comments, markdown formatting, or surrounding instructions. The response should be directly executable when piped into a file. Make sure to include the sha-bang with a newline after it.

  - install-auditor:
You are an install file auditor. Your task is to analyze installation files from external sources for potential malicious code. Perform static analysis to identify suspicious patterns, check file signatures against known safe sources, and verify checksums to ensure file integrity. Report any anomalies or potential threats without providing explanations or additional context.

  - code-commentor:
You are a code commentor.  For any given code snippet, provide detail explanations for each line of code, including the purpose of the line, how it works, and its contribution to the overall functionality of the system.  Ensure that the explanations are clear and concise, and maintain a logical flow, that helps the reader understand the code in context.  Return only the code with comments, without any addition formatting or extraneous text.
```

### Code Generator
1. Use systesm 'code-generator' to find large files
   ```
   $ vern --use-sys code-generator Create a bash script which finds the 10 biggest files recursively and takes a dir as an arg | tee find_large_files.sh
   #!/bin/bash

   dir="$1"

   if [ -z "$dir" ]; then
     echo "Usage: $0 <directory>"
     exit 1
   fi

   find "$dir" -type f -exec du -h {} + | sort -hr | head -n 10

   $ chmod +x find_large_files.sh
   $ ./find_large_files.sh ~/Downloads
   7.5G    /home/rgrimm/Downloads/iso-img/iso/ArkOS_RG353M_v2.0_11182022.img
   5.8G    /home/rgrimm/Downloads/iso-img/Win10_22H2_English_x64v1.iso
   5.7G    /home/rgrimm/Downloads/iso-img/iso/ubuntu-24.04-desktop-amd64.iso
   4.7G    /home/rgrimm/Downloads/iso-img/iso/ubuntu-22.04.3-desktop-amd64.iso
   3.8G    /home/rgrimm/Downloads/iso-img/xubuntu-24.04-desktop-amd64.iso
   2.9G    /home/rgrimm/Downloads/iso-img/iso/lubuntu-23.04-desktop-amd64.iso
   2.9G    /home/rgrimm/Downloads/iso-img/iso/linuxmint-21.3-cinnamon-64bit.iso
   2.7G    /home/rgrimm/Downloads/iso-img/linuxmint-22-xfce-64bit.iso
   2.5G    /home/rgrimm/Downloads/iso-img/iso/Manjaro-ARM-RoninOS-rockpro64-22.12.img
   1.9G    /home/rgrimm/Downloads/iso-img/iso/rockpi4c_ubuntu_focal_server_arm64_20210126_0004-gpt.img
   ```

### Code commentor

1.  wget pow.cpp from bitcoin core
   ``` bash
   wget [https://github.com/bitcoin/bitcoin/blob/master/src/pow.cpp](https://raw.githubusercontent.com/bitcoin/bitcoin/refs/heads/master/src/pow.cpp)
   ```
2.  Use code-commentor system and pipe in pow.cpp
   ```
   cat pow.cpp|vern --stdin --use-sys code-commentor|tee pow-commented.cpp
   ```
You should see something like
``` cpp
// Copyright (c) 2009-2010 Satoshi Nakamoto
// Copyright (c) 2009-2022 The Bitcoin Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <pow.h>

#include <arith_uint256.h>
#include <chain.h>
#include <primitives/block.h>
#include <uint256.h>
#include <util/check.h>

// Function to determine the next required proof of work difficulty
unsigned int GetNextWorkRequired(const CBlockIndex* pindexLast, const CBlockHeader *pblock, const Consensus::Params& params)
{
    // Ensure the last block index is not null
    assert(pindexLast != nullptr);

    // Get the proof of work limit in compact form
    unsigned int nProofOfWorkLimit = UintToArith256(params.powLimit).GetCompact();

    // Check if we are at a difficulty adjustment interval
    if ((pindexLast->nHeight+1) % params.DifficultyAdjustmentInterval() != 0)
    {
        // Special rules for testnet allowing minimum difficulty blocks
        if (params.fPowAllowMinDifficultyBlocks)
        {
            // If the new block's timestamp is more than twice the target spacing, allow a min-difficulty block
            if (pblock->GetBlockTime() > pindexLast->GetBlockTime() + params.nPowTargetSpacing*2)
                return nProofOfWorkLimit;
            else
            {
                // Return the last non-special-min-difficulty-rules-block
                const CBlockIndex* pindex = pindexLast;
                while (pindex->pprev && pindex->nHeight % params.DifficultyAdjustmentInterval() != 0 && pindex->nBits == nProofOfWorkLimit)
                    pindex = pindex->pprev;
                return pindex->nBits;
            }
        }
        // Return the difficulty of the last block
        return pindexLast->nBits;
    }

    // Calculate the first block of the difficulty adjustment period
    int nHeightFirst = pindexLast->nHeight - (params.DifficultyAdjustmentInterval()-1);
    assert(nHeightFirst >= 0);
    const CBlockIndex* pindexFirst = pindexLast->GetAncestor(nHeightFirst);
    assert(pindexFirst);

    // Calculate the new difficulty
    return CalculateNextWorkRequired(pindexLast, pindexFirst->GetBlockTime(), params);
}
*** snip ***
```
Full output: https://github.com/rpgrimm/vern/blob/main/demos/output_samples/bitcoin-hash-comments.md

### Recipe generator

1.  Use system recipe generator 
```
$ ./client.py --new-s latex-recipe-generator "You are a LaTeX generator that formats recipes into well-structured LaTeX documents. Given a recipe title, a list of ingredients, and step-by-step instructions, output only valid LaTeX code with no explanations or comments.  Ensure the document uses "\\documentclass{article}", properly formatted sections, a clear ingredient list, and a numbered steps section for instructions."
```

2.  Ask it for a marinade with specific ingredients
```
$ vern --use-sys recipe-generator "I want a marinade for 2 pounds of skirt steak and I have worstechire sauce, soy sauce, lime juice, and garlic.  Make a recipe that shows all the preportions" | tee skirt-steak-marinade.latex

 \documentclass{article}
 \usepackage{geometry}
 \geometry{a4paper, margin=1in}
 \usepackage{enumitem}

 \title{Marinade for Skirt Steak}
 \author{}
 \date{}

 \begin{document}

 \maketitle

 \section*{Ingredients}
 \begin{itemize}
     \item 2 pounds of skirt steak
     \item \textbf{Marinade:}
     \begin{itemize}
         \item \(\frac{1}{4}\) cup Worcestershire sauce
         \item \(\frac{1}{4}\) cup soy sauce
         \item \(\frac{1}{4}\) cup lime juice
         \item 4 cloves of garlic, minced
     \end{itemize}
 \end{itemize}

 \section*{Instructions}
 \begin{enumerate}
     \item In a medium bowl, combine the Worcestershire sauce, soy sauce, lime juice, and minced garlic. Mix well to create the
 marinade.
     \item Place the skirt steak in a large resealable plastic bag or a shallow dish.
     \item Pour the marinade over the steak, ensuring it is evenly coated.
     \item Seal the bag or cover the dish with plastic wrap. Refrigerate for at least 2 hours, or overnight for best results.
     \item Preheat your grill or skillet over medium-high heat.
     \item Remove the steak from the marinade and let any excess marinade drip off.
     \item Grill or sear the steak for 3-5 minutes on each side, or until desired doneness is reached.
     \item Let the steak rest for 5 minutes before slicing against the grain.
 \end{enumerate}

 \end{document}
```
3.  Use pdflatex to create a pdf
```
$ pdflatex skirt-steak-marinade.latex
```
See https://github.com/rpgrimm/vern/blob/main/demos/output_samples/skirt-steak-marinade.pdf

4.  Ask if for a five pound version
```
$ vern --use-sys recipe-generator now give me a version for 5 pounds

 \documentclass{article}
 \usepackage{geometry}
 \geometry{a4paper, margin=1in}
 \usepackage{enumitem}

 \title{Marinade for Skirt Steak}
 \author{}
 \date{}

 \begin{document}

 \maketitle

 \section*{Ingredients}
 \begin{itemize}
     \item 5 pounds of skirt steak
     \item \textbf{Marinade:}
     \begin{itemize}
         \item \(\frac{5}{8}\) cup Worcestershire sauce
         \item \(\frac{5}{8}\) cup soy sauce
         \item \(\frac{5}{8}\) cup lime juice
         \item 10 cloves of garlic, minced
     \end{itemize}
 \end{itemize}

 \section*{Instructions}
 \begin{enumerate}
     \item In a medium bowl, combine the Worcestershire sauce, soy sauce, lime juice, and minced garlic. Mix well to create the marinade.
     \item Place the skirt steak in a large resealable plastic bag or a shallow dish.
     \item Pour the marinade over the steak, ensuring it is evenly coated.
     \item Seal the bag or cover the dish with plastic wrap. Refrigerate for at least 2 hours, or overnight for best results.
     \item Preheat your grill or skillet over medium-high heat.
     \item Remove the steak from the marinade and let any excess marinade drip off.
     \item Grill or sear the steak for 3-5 minutes on each side, or until desired doneness is reached.
     \item Let the steak rest for 5 minutes before slicing against the grain.
 \end{enumerate}

 \end{document}
```

### Modern Translator

1.  Reset session to avoid token limit and use modern translator
    ```
    vern --reset
    ```
2.  Run ../scripts/get_canterbury_tales_prologue.sh 
    ```
    $ ../scripts/get_canterbury_tales_prologue.sh
    ```
3.  Feed prologue to vern
    ```
    $ cat canterbury-tales-prologue.txt|vern --use-sys modern-translator --stdin | tee canterbury-tales-prologue-modern.txt
    ```
```
THE PROLOGUE

When April, with its sweet showers, has pierced the drought of March to the root and bathed every vein in such liquid that the flower is born from it; when the gentle west wind, Zephyrus,
has breathed life into the tender crops in every grove and field, and the young sun has run half its course in Aries, and small birds make melody, sleeping all night with open eyes, so
nature stirs them in their hearts; then people long to go on pilgrimages, and travelers seek distant shores to visit holy shrines in various lands. Especially from every corner of
England, they travel to Canterbury to seek the holy blessed martyr who has helped them when they were sick.

It happened that in this season, one day in Southwark at the Tabard Inn, as I lay ready to go on my pilgrimage to Canterbury with a devout heart, there came into that inn at night a
company of twenty-nine people, of various sorts, who had by chance fallen into fellowship, and they were all pilgrims who intended to ride to Canterbury. The rooms and stables were
spacious, and we were well provided with the best. Shortly, when the sun had set, I had spoken with every one of them, and I was soon part of their fellowship, and we made a promise to
rise early to take our way as I will describe to you.
*** snip ***
```
See the full output at https://github.com/rpgrimm/vern/blob/main/demos/output_samples/canterbury-tales-prologue-modern.txt
