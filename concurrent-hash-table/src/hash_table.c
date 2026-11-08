#include "hash_table.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

HashTable* hash_table_create(uint64_t size) {
    HashTable *ht = malloc(sizeof(HashTable));
    if (!ht) return NULL;
    
    ht->size = size;
    ht->buckets = calloc(size, sizeof(HashNode*));
    if (!ht->buckets) {
        free(ht);
        return NULL;
    }
    
    ht->locks = malloc(size * sizeof(pthread_mutex_t));
    if (!ht->locks) {
        free(ht->buckets);
        free(ht);
        return NULL;
    }
    
    for (uint64_t i = 0; i < size; i++) {
        pthread_mutex_init(&ht->locks[i], NULL);
    }
    return ht;
}

// Djb2 hash function
uint64_t djb2_hash(char *str, uint64_t table_size) {
    uint64_t hash = 5381;
    int c;
    while ((c = *str++)) {
        hash = ((hash << 5) + hash) + c; // hash * 33 + c
    }
    return hash % table_size;
}

bool hash_table_insert(HashTable *ht, char *key, uint64_t *index, uint64_t *collision_count) {
    uint64_t bucket_index = djb2_hash(key, ht->size);
    *index = bucket_index;
    
    pthread_mutex_lock(&ht->locks[bucket_index]);
    
    HashNode *node = ht->buckets[bucket_index];
    
    while (node != NULL) {
        if (strcmp(node->key, key) == 0) {
            if (node->deleted) {
                node->deleted = false;
                *index = node->index;
                pthread_mutex_unlock(&ht->locks[bucket_index]);
                return false;
            } else {
                *index = node->index;
                pthread_mutex_unlock(&ht->locks[bucket_index]);
                return true;
            }
        }
        node = node->next;
        if (node != NULL) {
            (*collision_count)++;
        }
    }
    
    HashNode *new_node = malloc(sizeof(HashNode));
    if (!new_node) {
        pthread_mutex_unlock(&ht->locks[bucket_index]);
        return false;
    }
    
    new_node->key = strdup(key);
    new_node->index = bucket_index;
    new_node->deleted = false;
    new_node->next = ht->buckets[bucket_index];
    ht->buckets[bucket_index] = new_node;
    
    *index = bucket_index;
    pthread_mutex_unlock(&ht->locks[bucket_index]);
    return false;
}

bool hash_table_delete(HashTable *ht, char *key, uint64_t *index, uint64_t *collision_count) {
    uint64_t bucket_index = djb2_hash(key, ht->size);
    
    pthread_mutex_lock(&ht->locks[bucket_index]);
    
    HashNode *node = ht->buckets[bucket_index];
    
    while (node != NULL) {
        if (strcmp(node->key, key) == 0) {
            if (!node->deleted) {
                node->deleted = true;
                *index = node->index;
                pthread_mutex_unlock(&ht->locks[bucket_index]);
                return true;
            } else {
                pthread_mutex_unlock(&ht->locks[bucket_index]);
                return false;
            }
        }
        node = node->next;
        if (node != NULL) {
            (*collision_count)++;
        }
    }
    
    pthread_mutex_unlock(&ht->locks[bucket_index]);
    return false;
}

void hash_table_destroy(HashTable *ht) {
    if (!ht) return;
    
    for (uint64_t i = 0; i < ht->size; i++) {
        HashNode *node = ht->buckets[i];
        while (node != NULL) {
            HashNode *temp = node;
            node = node->next;
            free(temp->key);
            free(temp);
        }
        pthread_mutex_destroy(&ht->locks[i]);
    }
    free(ht->buckets);
    free(ht->locks);
    free(ht);
}