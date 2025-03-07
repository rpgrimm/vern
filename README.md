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
```

```cpp
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

// Function to calculate the next work required based on the last block and the first block time
unsigned int CalculateNextWorkRequired(const CBlockIndex* pindexLast, int64_t nFirstBlockTime, const Consensus::Params& params)
{
    // If no retargeting is allowed, return the last block's difficulty
    if (params.fPowNoRetargeting)
        return pindexLast->nBits;

    // Calculate the actual timespan between the first and last block
    int64_t nActualTimespan = pindexLast->GetBlockTime() - nFirstBlockTime;

    // Limit the adjustment step to prevent extreme difficulty changes
    if (nActualTimespan < params.nPowTargetTimespan/4)
        nActualTimespan = params.nPowTargetTimespan/4;
    if (nActualTimespan > params.nPowTargetTimespan*4)
        nActualTimespan = params.nPowTargetTimespan*4;

    // Calculate the new difficulty target
    const arith_uint256 bnPowLimit = UintToArith256(params.powLimit);
    arith_uint256 bnNew;

    // Special rule for Testnet4
    if (params.enforce_BIP94) {
        // Use the first block of the difficulty period to preserve real difficulty
        int nHeightFirst = pindexLast->nHeight - (params.DifficultyAdjustmentInterval()-1);
        const CBlockIndex* pindexFirst = pindexLast->GetAncestor(nHeightFirst);
        bnNew.SetCompact(pindexFirst->nBits);
    } else {
        bnNew.SetCompact(pindexLast->nBits);
    }

    // Adjust the difficulty based on the actual timespan
    bnNew *= nActualTimespan;
    bnNew /= params.nPowTargetTimespan;

    // Ensure the new difficulty does not exceed the proof of work limit
    if (bnNew > bnPowLimit)
        bnNew = bnPowLimit;

    // Return the new difficulty in compact form
    return bnNew.GetCompact();
}

// Function to check if the difficulty transition is permitted
bool PermittedDifficultyTransition(const Consensus::Params& params, int64_t height, uint32_t old_nbits, uint32_t new_nbits)
{
    // Allow all transitions if minimum difficulty blocks are allowed
    if (params.fPowAllowMinDifficultyBlocks) return true;

    // Check if we are at a difficulty adjustment interval
    if (height % params.DifficultyAdjustmentInterval() == 0) {
        // Define the smallest and largest timespan for difficulty adjustment
        int64_t smallest_timespan = params.nPowTargetTimespan/4;
        int64_t largest_timespan = params.nPowTargetTimespan*4;

        // Get the proof of work limit
        const arith_uint256 pow_limit = UintToArith256(params.powLimit);
        arith_uint256 observed_new_target;
        observed_new_target.SetCompact(new_nbits);

        // Calculate the largest difficulty target possible
        arith_uint256 largest_difficulty_target;
        largest_difficulty_target.SetCompact(old_nbits);
        largest_difficulty_target *= largest_timespan;
        largest_difficulty_target /= params.nPowTargetTimespan;

        // Ensure the largest difficulty target does not exceed the proof of work limit
        if (largest_difficulty_target > pow_limit) {
            largest_difficulty_target = pow_limit;
        }

        // Compare the observed new target with the maximum new target
        arith_uint256 maximum_new_target;
        maximum_new_target.SetCompact(largest_difficulty_target.GetCompact());
        if (maximum_new_target < observed_new_target) return false;

        // Calculate the smallest difficulty target possible
        arith_uint256 smallest_difficulty_target;
        smallest_difficulty_target.SetCompact(old_nbits);
        smallest_difficulty_target *= smallest_timespan;
        smallest_difficulty_target /= params.nPowTargetTimespan;

        // Ensure the smallest difficulty target does not exceed the proof of work limit
        if (smallest_difficulty_target > pow_limit) {
            smallest_difficulty_target = pow_limit;
        }

        // Compare the observed new target with the minimum new target
        arith_uint256 minimum_new_target;
        minimum_new_target.SetCompact(smallest_difficulty_target.GetCompact());
        if (minimum_new_target > observed_new_target) return false;
    } else if (old_nbits != new_nbits) {
        // If not at a difficulty adjustment interval, the difficulty should not change
        return false;
    }
    return true;
}

// Function to check proof of work during fuzz testing
bool CheckProofOfWork(uint256 hash, unsigned int nBits, const Consensus::Params& params)
{
    // Simplified validation for fuzz testing
    if constexpr (G_FUZZING) return (hash.data()[31] & 0x80) == 0;
    // Use the standard proof of work implementation
    return CheckProofOfWorkImpl(hash, nBits, params);
}

// Function to derive the target from nBits and the proof of work limit
std::optional<arith_uint256> DeriveTarget(unsigned int nBits, const uint256 pow_limit)
{
    bool fNegative;
    bool fOverflow;
    arith_uint256 bnTarget;

    // Convert nBits to an arith_uint256 target
    bnTarget.SetCompact(nBits, &fNegative, &fOverflow);

    // Check if the target is valid
    if (fNegative || bnTarget == 0 || fOverflow || bnTarget > UintToArith256(pow_limit))
        return {};

    return bnTarget;
}

// Implementation of the proof of work check
bool CheckProofOfWorkImpl(uint256 hash, unsigned int nBits, const Consensus::Params& params)
{
    // Derive the target from nBits
    auto bnTarget{DeriveTarget(nBits, params.powLimit)};
    if (!bnTarget) return false;

    // Check if the hash is less than or equal to the target
    if (UintToArith256(hash) > bnTarget)
        return false;

    return true;
}
```

This code is a part of the Bitcoin Core software, specifically dealing with the proof of work (PoW) difficulty adjustment mechanism. The comments added provide explanations for each function and key logic blocks, helping readers understand the purpose and functionality of the code.


### Translating old texts

1.  wget Chaucer's  
```
wget https://www.gutenberg.org/cache/epub/2383/pg2383.txt
```

See demos for more use cases such as commenting code, auditing /etc/ssh files,
creating bash scripts, making notes on old books, creating recipes and showing
markdown, and more.
