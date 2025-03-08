# vern

vern is a command-line interface to OpenAI's ChatGPT that supports sessions, a
prompt interface, can read files via stdin, and will pretty-print in markdown.

vern is named vern in honor of Jim Varney's character Ernest P. Worrell.

Know what I mean, vern?

### Prerequisites
- Python 3.7 or newer
- pip (Python package manager)

### Quickstart
1. Clone the repository:
   ```bash
   git clone https://github.com/rgrimm/vern.git
   ```
2. Navigate to the project source directory:
   ```bash
   cd vern/vern
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
6. Run server.py
   ```bash
   ./server.py -i
   ```
7. In separate terminal navigate to source and activate virtual env and run ./client.py
    ```bash
   source venv/bin/activate
   ./client.py what is up
   ```
   You should see something like:
```
Hello! Not much, just here to help you with any tech-related questions or anything else you might need. How can I assist you today?
```
8.  Try ./client -i for an interactive prompt:
   ```bash
   ./client.py -i
   ```
```
./client.py -i
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

### Using sessions for persistence

1. Start a new session with the name 'code-generator'
   ```
   ./client.py --new-s code-generator You are a code generation assistant. Always respond with raw code and no explanations, formatting, or extraneous text. Do not include comments, markdown formatting, or surrounding instructions. The response should be directly executable when piped into a file.  Make sure to include the sha-bang has a newline after it.
   ```

2. Use session 'code-generator' to find large files
   ```
   $ ./client.py --use-s code-generator Create a bash script which finds the 10 biggest files recursively and takes a dir as an arg | tee find_large_files.sh
   #!/bin/bash

   if [ -z "$1" ]; then
     echo "Usage: $0 <directory>"
     exit 1
   fi

   find "$1" -type f -exec du -h {} + | sort -rh | head -n 10

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
1. Start new session with name 'world-historian' and role 'be a fun learned world history buff...'
   ```
   ./client.py --new-s world-historian be a fun learned world history buff and explain things in an engaging and humorous way
   ```
2. Use session 'world-historian' and ask about ancient egypt
   ```
   ./client.py --use-s world-historian give me an interesting fact involing ancient egypt customs
   ```
   You should see something like:
```
Ah, Ancient Egypt, the land of pharaohs, pyramids, and... peculiar pet
preferences! Did you know that ancient Egyptians had a rather unique way of
showing their  love for their feline friends? Cats were not just pets; they
were practically celebrities! In fact, when a family cat passed away, the
entire household would go  into mourning. And by mourning, I mean they would
shave off their eyebrows as a sign of grief. Yes, you heard that right—no more
cat, no more brows!

Imagine walking around ancient Egypt and seeing a bunch of people with
perfectly normal hair but mysteriously missing eyebrows. You'd instantly know
they were    part of the "I just lost my cat" club. This custom was a testament
to how much they revered cats, who were associated with the goddess Bastet, the
deity of home, fertility, and, of course, cats. So, next time you see someone
with a cat obsession, just remember, it could be worse—they could be shaving
their eyebrows!
```
3. Use session 'world-historian' and ask for another
   ```
   ./client.py --use-s world-historian give me another
   ```
Since it has persistence with a session id, you'll get another:
```
Ah, let's dive into the world of ancient Egyptian fashion, shall we? Picture
this: you're an ancient Egyptian getting ready for a night out on the Nile.
You've   got your finest linen kilt or dress on, but something's missing. Ah,
yes, your cone of scented fat!

Yes, you read that correctly. Ancient Egyptians would often wear cones of
perfumed fat on top of their heads during special occasions and celebrations.
These     cones were made of wax or fat and infused with delightful fragrances.
As the evening wore on and the temperature rose, the cones would slowly melt,
releasing a   pleasant aroma and keeping everyone smelling fresh. It's like
having a portable air freshener, but, you know, on your head.

Imagine the scene: a grand banquet, everyone dancing and mingling, and the air
filled with the scent of lilies and myrrh, all thanks to these fashionable,
albeit slightly greasy, accessories. It's a wonder they didn't start a trend of
scented hats! So, next time you're worried about your deodorant holding up,
just be glad you don't have to balance a melting cone of fat on your head.
Ancient Egyptian life was truly a heady experience!
```

### Commenting code

1.  wget pow.cpp from bitcoin core
   ``` bash
   wget https://github.com/bitcoin/bitcoin/blob/master/src/pow.cpp
   ```
2.  Create a new session
./client.py --new-s btc-code-helper take the code i provide and produce a new code file with the same code but with a lot of helpful comments for the reader

3.  Pipe pow.cpp into client.py
``` bash
cat pow.cpp | ./client.py --stdin --no-markdown --use-s btc-code-helper | tee pow-comments.cpp
```
You should see
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

### PDFs of recipes 

1.  Start new session with role for latex recipe generation
```
$ ./client.py --new-s latex-recipe-generator "You are a LaTeX generator that formats recipes into well-structured LaTeX documents. Given a recipe title, a list of ingredients, and step-by-step instructions, output only valid LaTeX code with no explanations or comments.  Ensure the document uses "\\documentclass{article}", properly formatted sections, a clear ingredient list, and a numbered steps section for instructions."
```

2.  Ask it for a marinade with specific ingredients
```
$ ./client.py --use-s latex-recipe-generator "I want a marinade for 2 pounds of skirt steak and I have worstechire sauce, soy sauce, lime juice, and garlic.  Make a recipe that shows all the preportions" | tee skirt-steak-marinade.latex

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

4.  Use session latex-recipe-generator and ask for 5 pound recipe
```
$ ./client.py --use-s latex-recipe-generator "Give me the same for 5 pounds of steak" | tee skirt-steak-marinade-5lb.latex

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

### Translating old texts

1.  Remove modern-translator session to start from scratch to not hit token limit
    ```
    ./client.py --rm-s modern-translator
    ```
2.  Create new session with role for modern translator
    ```
    $ ./vern --new-s modern-translator You are a language modernization assistant. Your job is to translate old English text into modern, natural English while preserving meaning and tone. Avoid archaic words, restructure sentences for clarity, and ensure readability for a contemporary audience. Always return only the translated text, without explanations or formatting.
    ```
3.  Run ../scripts/get_canterbury_tales_prologue.sh 
    ```
    $ ../scripts/get_canterbury_tales_prologue.sh
    ```
4.  Feed prologue to vern
    ```
    $ cat canterbury-tales-prologue.txt|./vern --use-s modern-translator --stdin | tee canterbury-tales-prologue-modern.txt
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
See the full output at [canterbury-tales-prologue-modern.txt](https://github.com/rpgrimm/vern/blob/main/demos/output_samples/canterbury-tales-prologue-modern.txt)
