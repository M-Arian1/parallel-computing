#ifndef HASH_TABLE_H
#define HASH_TABLE_H

#include <stdint.h>
#include <pthread.h>
#include <stdbool.h>

#define MAX_THREADS 8192

typedef struct HashNode {
    char *key;
    uint64_t index;
    bool deleted;
    struct HashNode *next;
} HashNode;

typedef struct {
    HashNode **buckets;
    uint64_t size;
    pthread_mutex_t *locks;
} HashTable;

HashTable* hash_table_create(uint64_t size);
bool hash_table_insert(HashTable *ht, char *key, uint64_t *index, uint64_t *collision_count);
bool hash_table_delete(HashTable *ht, char *key, uint64_t *index, uint64_t *collision_count);
uint64_t djb2_hash(char *str, uint64_t table_size);
void hash_table_destroy(HashTable *ht);

#endif