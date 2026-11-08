#include "hash_table.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <time.h>
#include <sys/time.h>
#include <sys/stat.h>

typedef struct {
    char **data;
    uint64_t start;
    uint64_t end;
    HashTable *ht;
    uint64_t *collision_count;
    uint64_t *indices;
    char *flags;
    char *operation;
} ThreadData;

void* process_data(void *arg) {
    ThreadData *td = (ThreadData*) arg;
    
    for (uint64_t i = td->start; i < td->end; i++) {
        uint64_t local_collisions = 0;
        uint64_t index;
        bool existed;
        
        if (strcmp(td->operation, "insert") == 0) {
            existed = hash_table_insert(td->ht, td->data[i], &index, &local_collisions);
            td->indices[i] = index;
            td->flags[i] = existed ? 'T' : 'F';
        } else if (strcmp(td->operation, "delete") == 0) {
            existed = hash_table_delete(td->ht, td->data[i], &index, &local_collisions);
            td->indices[i] = index;
            td->flags[i] = existed ? 'T' : 'F';
        }
        
        __sync_add_and_fetch(td->collision_count, local_collisions);
    }
    return NULL;
}

uint64_t parse_size(const char *str) {
    char *end;
    uint64_t val = strtoull(str, &end, 10);
    if (*end == 'K' || *end == 'k') val *= 1000;
    else if (*end == 'M' || *end == 'm') val *= 1000000;
    return val;
}

char** read_input_file(const char *filename, uint64_t data_count, uint64_t *read_count) {
    FILE *fp = fopen(filename, "r");
    if (!fp) {
        fprintf(stderr, "Error: Cannot open file %s\n", filename);
        return NULL;
    }
    
    char **data = malloc(data_count * sizeof(char*));
    if (!data) {
        fclose(fp);
        return NULL;
    }
    
    char buffer[256];
    uint64_t i = 0;
    while (i < data_count && fgets(buffer, sizeof(buffer), fp)) {
        buffer[strcspn(buffer, "\n")] = 0;
        data[i++] = strdup(buffer);
    }
    *read_count = i;  /* a file may hold fewer lines than --data_size */
    fclose(fp);
    return data;
}

void free_data(char **data, uint64_t count) {
    for (uint64_t i = 0; i < count; i++) {
        free(data[i]);
    }
    free(data);
}

double get_time_diff(struct timeval start, struct timeval end) {
    return (end.tv_sec - start.tv_sec) * 1000.0 + 
           (end.tv_usec - start.tv_usec) / 1000.0;
}

int main(int argc, char *argv[]) {
    char *data_size_str = "150K";
    int threads = 1;
    char *tsize_str = "300K";
    char *flow_actions[16];
    char *input_files[16];
    int num_operations = 0;
    
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--data_size") == 0) {
            data_size_str = argv[++i];
        } else if (strcmp(argv[i], "--threads") == 0) {
            threads = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--tsize") == 0) {
            tsize_str = argv[++i];
        } else if (strcmp(argv[i], "--flow") == 0) {
            i++;
            while (i < argc && argv[i][0] != '-') {
                flow_actions[num_operations++] = argv[i++];
            }
            i--;
        } else if (strcmp(argv[i], "--input") == 0) {
            i++;
            for (int j = 0; j < num_operations && i < argc; j++) {
                input_files[j] = argv[i++];
            }
            i--;
        }
    }
    
    uint64_t data_count = parse_size(data_size_str);
    uint64_t table_size = parse_size(tsize_str);
    
    HashTable *ht = hash_table_create(table_size);
    if (!ht) {
        fprintf(stderr, "Error: Failed to create hash table\n");
        return 1;
    }
    
    mkdir("results", 0755);
    
    char flow_str[256] = {0};
    for (int i = 0; i < num_operations; i++) {
        strcat(flow_str, flow_actions[i]);
        if (i < num_operations - 1) strcat(flow_str, "_");
    }
    
    char output_filename[512];
    snprintf(output_filename, sizeof(output_filename), 
             "results/results_%s_%d_%s_%s.txt",
             data_size_str, threads, tsize_str, flow_str);
    
    FILE *output_file = fopen(output_filename, "w");
    if (!output_file) {
        fprintf(stderr, "Error: Cannot create output file\n");
        hash_table_destroy(ht);
        return 1;
    }
    
    for (int op = 0; op < num_operations; op++) {
        printf("Processing operation %d: %s on file %s\n", op + 1, flow_actions[op], input_files[op]);
        
        uint64_t n = 0;
        char **data = read_input_file(input_files[op], data_count, &n);
        if (!data) {
            fprintf(stderr, "Error: Failed to read input file %s\n", input_files[op]);
            continue;
        }
        
        uint64_t *indices = malloc(n * sizeof(uint64_t));
        char *flags = malloc(n * sizeof(char));
        uint64_t collision_count = 0;
        
        struct timeval start_time, end_time;
        gettimeofday(&start_time, NULL);
        
        if (threads == 1) {
            ThreadData td = {data, 0, n, ht, &collision_count, indices, flags, flow_actions[op]};
            process_data(&td);
        } else {
            pthread_t thread_pool[MAX_THREADS];
            ThreadData thread_args[MAX_THREADS];
            uint64_t chunk_size = n / threads;
            
            for (int i = 0; i < threads; i++) {
                thread_args[i].data = data;
                thread_args[i].start = i * chunk_size;
                thread_args[i].end = (i == threads - 1) ? n : (i + 1) * chunk_size;
                thread_args[i].ht = ht;
                thread_args[i].collision_count = &collision_count;
                thread_args[i].indices = indices;
                thread_args[i].flags = flags;
                thread_args[i].operation = flow_actions[op];
                pthread_create(&thread_pool[i], NULL, process_data, &thread_args[i]);
            }
            
            for (int i = 0; i < threads; i++) {
                pthread_join(thread_pool[i], NULL);
            }
        }
        
        gettimeofday(&end_time, NULL);
        double exec_time = get_time_diff(start_time, end_time);
        
        fprintf(output_file, "Actions: %s\n", flow_actions[op]);
        fprintf(output_file, "ExecutionTime: %.2f ms\n", exec_time);
        fprintf(output_file, "NumberOfHandledCollision: %lu\n", collision_count);
        
        fprintf(output_file, "Data:");
        for (uint64_t i = 0; i < n; i++) {
            if (strcmp(flow_actions[op], "delete") == 0 && flags[i] == 'F') {
                fprintf(output_file, "%s:F", data[i]);
            } else {
                fprintf(output_file, "%s:%lu:%c", data[i], indices[i], flags[i]);
            }
            if (i < n - 1) fprintf(output_file, ",");
        }
        fprintf(output_file, "\n\n");
        
        // Clean up
        free_data(data, n);
        free(indices);
        free(flags);
    }
    
    fclose(output_file);
    hash_table_destroy(ht);
    
    return 0;
}