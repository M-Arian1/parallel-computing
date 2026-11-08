#include <stdio.h>
#include <time.h>
#include <malloc.h>
#include <math.h>
#include <stdlib.h>


#define MATDIM 10240

#define cudaCheckError() {                                                                     \
    cudaError_t error = cudaGetLastError();                                                    \
    if (error != cudaSuccess) {                                                                \
        printf("Cuda failure %s:%d: '%s'\n", __FILE__, __LINE__, cudaGetErrorString(error));   \
        exit(1);                                                                               \
    }                                                                                          \
}


__global__ void multiplymat(float *a, float* b, float* ans){
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int column = blockIdx.x * blockDim.x + threadIdx.x;

    float sum = 0;
    for(int i=0;i< MATDIM; i++){
        sum += a[MATDIM * row + i] * b[MATDIM * i + column];
    }

    ans[MATDIM * row + column] = sum;
    __syncthreads();
}



void matmake(float* a){
    for(int i=0;i< MATDIM ;i++){
        for(int j=0;j< MATDIM ;j++){
            a[MATDIM*i+j] = 1;
        }
    }
}



int main(){
    int matsize = MATDIM * MATDIM * sizeof(float);
    clock_t starttime, endtime;
    float* a;
    float* b;
    float* ans;
    a = (float*) malloc(matsize);
    matmake(a);
    b = (float*) malloc(matsize);
    matmake(b);
    ans = (float*) malloc(matsize);


    float* a_dev;
    float* b_dev;
    float* ans_dev;
    cudaMalloc(&a_dev, matsize);
    cudaMalloc(&b_dev, matsize);
    cudaMalloc(&ans_dev, matsize);
    
    cudaMemcpy(a_dev, a, matsize, cudaMemcpyHostToDevice);
    cudaMemcpy(b_dev, b, matsize, cudaMemcpyHostToDevice);



    starttime = clock();
    int thread_size = 320;
    dim3 threadd(thread_size, thread_size, 1);
    dim3 blockd(MATDIM / thread_size, MATDIM / thread_size, 1);
    multiplymat<<<threadd, blockd>>>(a_dev, b_dev, ans_dev);
    

    cudaMemcpy(ans, ans_dev, matsize, cudaMemcpyDeviceToHost);
    endtime = clock();

    int ww = 0;
    for(int i=0;i<MATDIM;i++){
        for(int j=0;j<MATDIM;j++){
            if(abs(ans[i*MATDIM + j]-MATDIM) > 0.01){
                ww += 1;
            }
            
        }
    }
    printf("wrongs:%d\n", ww);



    free(a);
    free(b);
    free(ans);
    cudaFree(a_dev);
    cudaFree(b_dev);
    cudaFree(ans_dev);
    printf("time: %f", (double)(endtime - starttime)/CLOCKS_PER_SEC);
    cudaCheckError();
}