```cpp
// Copyright (c) 2013-2022 The Bitcoin Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <hash.h> // Include the hash header for hash-related functions and classes
#include <span.h> // Include the span header for handling spans of data
#include <crypto/common.h> // Include common cryptographic utilities
#include <crypto/hmac_sha512.h> // Include HMAC-SHA512 cryptographic functions

#include <bit> // Include bit manipulation utilities
#include <string> // Include string utilities

// Function to compute a MurmurHash3 hash, which is a non-cryptographic hash function
unsigned int MurmurHash3(unsigned int nHashSeed, Span<const unsigned char> vDataToHash)
{
    // Initialize hash value with the seed
    uint32_t h1 = nHashSeed;
    // Constants used in the MurmurHash3 algorithm
    const uint32_t c1 = 0xcc9e2d51;
    const uint32_t c2 = 0x1b873593;

    // Calculate the number of 4-byte blocks in the data
    const int nblocks = vDataToHash.size() / 4;

    //----------
    // body
    // Pointer to the start of the data blocks
    const uint8_t* blocks = vDataToHash.data();

    // Process each 4-byte block
    for (int i = 0; i < nblocks; ++i) {
        // Read a 4-byte block as a little-endian integer
        uint32_t k1 = ReadLE32(blocks + i*4);

        // Mix the block into the hash
        k1 *= c1;
        k1 = std::rotl(k1, 15);
        k1 *= c2;

        h1 ^= k1;
        h1 = std::rotl(h1, 13);
        h1 = h1 * 5 + 0xe6546b64;
    }

    //----------
    // tail
    // Pointer to the remaining bytes after the last full block
    const uint8_t* tail = vDataToHash.data() + nblocks * 4;

    uint32_t k1 = 0;

    // Process the remaining bytes (less than 4)
    switch (vDataToHash.size() & 3) {
        case 3:
            k1 ^= tail[2] << 16;
            [[fallthrough]];
        case 2:
            k1 ^= tail[1] << 8;
            [[fallthrough]];
        case 1:
            k1 ^= tail[0];
            k1 *= c1;
            k1 = std::rotl(k1, 15);
            k1 *= c2;
            h1 ^= k1;
    }

    //----------
    // finalization
    // Finalize the hash value
    h1 ^= vDataToHash.size();
    h1 ^= h1 >> 16;
    h1 *= 0x85ebca6b;
    h1 ^= h1 >> 13;
    h1 *= 0xc2b2ae35;
    h1 ^= h1 >> 16;

    // Return the final hash value
    return h1;
}

// Function to compute a BIP32 hash, which is used in the Bitcoin protocol for hierarchical deterministic wallets
void BIP32Hash(const ChainCode &chainCode, unsigned int nChild, unsigned char header, const unsigned char data[32], unsigned char output[64])
{
    unsigned char num[4];
    // Write the child number as a big-endian 4-byte integer
    WriteBE32(num, nChild);
    // Create an HMAC-SHA512 object and write the header, data, and child number to it, then finalize the hash
    CHMAC_SHA512(chainCode.begin(), chainCode.size()).Write(&header, 1).Write(data, 32).Write(num, 4).Finalize(output);
}

// Function to compute a SHA256 hash of a uint256 object
uint256 SHA256Uint256(const uint256& input)
{
    uint256 result;
    // Create a SHA256 object, write the input data to it, and finalize the hash
    CSHA256().Write(input.begin(), 32).Finalize(result.begin());
    // Return the resulting hash
    return result;
}

// Function to create a tagged hash writer, which is used in Bitcoin for domain separation in hash functions
HashWriter TaggedHash(const std::string& tag)
{
    HashWriter writer{};
    uint256 taghash;
    // Compute the SHA256 hash of the tag
    CSHA256().Write((const unsigned char*)tag.data(), tag.size()).Finalize(taghash.begin());
    // Write the tag hash twice to the hash writer for domain separation
    writer << taghash << taghash;
    // Return the hash writer
    return writer;
}
```

This code provides implementations of various hash functions used in the Bitcoin protocol, including MurmurHash3, BIP32 hash, SHA256 hash, and a tagged hash writer for domain separation. Each function is carefully designed to meet specific requirements of the Bitcoin protocol, such as non-cryptographic hashing, hierarchical deterministic wallet derivation, and domain separation in hash functions.

```
(venv) ➜  rgrimm ripper ~/code/dev/vern/vern git:(master) ✗ diff -u hash.cpp hash-commented.cpp
--- hash.cpp    2025-03-06 10:12:59.131505679 -0500
+++ hash-commented.cpp  2025-03-06 10:15:05.840753387 -0500
@@ -1,31 +1,39 @@
+```cpp
 // Copyright (c) 2013-2022 The Bitcoin Core developers
 // Distributed under the MIT software license, see the accompanying
 // file COPYING or http://www.opensource.org/licenses/mit-license.php.

-#include <hash.h>
-#include <span.h>
-#include <crypto/common.h>
-#include <crypto/hmac_sha512.h>
+#include <hash.h> // Include the hash header for hash-related functions and classes
+#include <span.h> // Include the span header for handling spans of data
+#include <crypto/common.h> // Include common cryptographic utilities
+#include <crypto/hmac_sha512.h> // Include HMAC-SHA512 cryptographic functions

-#include <bit>
-#include <string>
+#include <bit> // Include bit manipulation utilities
+#include <string> // Include string utilities

+// Function to compute a MurmurHash3 hash, which is a non-cryptographic hash function
 unsigned int MurmurHash3(unsigned int nHashSeed, Span<const unsigned char> vDataToHash)
 {
-    // The following is MurmurHash3 (x86_32), see https://github.com/aappleby/smhasher/blob/master/src/MurmurHash3.cpp
+    // Initialize hash value with the seed
     uint32_t h1 = nHashSeed;
+    // Constants used in the MurmurHash3 algorithm
     const uint32_t c1 = 0xcc9e2d51;
     const uint32_t c2 = 0x1b873593;

+    // Calculate the number of 4-byte blocks in the data
     const int nblocks = vDataToHash.size() / 4;

     //----------
     // body
+    // Pointer to the start of the data blocks
     const uint8_t* blocks = vDataToHash.data();

+    // Process each 4-byte block
     for (int i = 0; i < nblocks; ++i) {
+        // Read a 4-byte block as a little-endian integer
         uint32_t k1 = ReadLE32(blocks + i*4);

+        // Mix the block into the hash
         k1 *= c1;
         k1 = std::rotl(k1, 15);
         k1 *= c2;
@@ -37,10 +45,12 @@

     //----------
     // tail
+    // Pointer to the remaining bytes after the last full block
     const uint8_t* tail = vDataToHash.data() + nblocks * 4;

     uint32_t k1 = 0;

+    // Process the remaining bytes (less than 4)
     switch (vDataToHash.size() & 3) {
         case 3:
             k1 ^= tail[2] << 16;
@@ -58,6 +68,7 @@

     //----------
     // finalization
+    // Finalize the hash value
     h1 ^= vDataToHash.size();
     h1 ^= h1 >> 16;
     h1 *= 0x85ebca6b;
@@ -65,28 +76,42 @@
     h1 *= 0xc2b2ae35;
     h1 ^= h1 >> 16;

+    // Return the final hash value
     return h1;
 }

+// Function to compute a BIP32 hash, which is used in the Bitcoin protocol for hierarchical deterministic wallets
 void BIP32Hash(const ChainCode &chainCode, unsigned int nChild, unsigned char header, const unsigned char data[32], unsigned char output[64])
 {
     unsigned char num[4];
+    // Write the child number as a big-endian 4-byte integer
     WriteBE32(num, nChild);
+    // Create an HMAC-SHA512 object and write the header, data, and child number to it, then finalize the hash
     CHMAC_SHA512(chainCode.begin(), chainCode.size()).Write(&header, 1).Write(data, 32).Write(num, 4).Finalize(output);
 }

+// Function to compute a SHA256 hash of a uint256 object
 uint256 SHA256Uint256(const uint256& input)
 {
     uint256 result;
+    // Create a SHA256 object, write the input data to it, and finalize the hash
     CSHA256().Write(input.begin(), 32).Finalize(result.begin());
+    // Return the resulting hash
     return result;
 }

+// Function to create a tagged hash writer, which is used in Bitcoin for domain separation in hash functions
 HashWriter TaggedHash(const std::string& tag)
 {
     HashWriter writer{};
     uint256 taghash;
+    // Compute the SHA256 hash of the tag
     CSHA256().Write((const unsigned char*)tag.data(), tag.size()).Finalize(taghash.begin());
+    // Write the tag hash twice to the hash writer for domain separation
     writer << taghash << taghash;
+    // Return the hash writer
     return writer;
 }
+```
+
+This code provides implementations of various hash functions used in the Bitcoin protocol, including MurmurHash3, BIP32 hash, SHA256 hash, and a tagged hash writer for domain separation. Each function is carefully designed to meet specific requirements of the Bitcoin protocol, such as non-cryptographic hashing, hierarchical deterministic wallet derivation, and domain separation in hash functions.
```
