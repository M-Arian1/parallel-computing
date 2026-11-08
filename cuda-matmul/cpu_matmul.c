#include <stdio.h>
#include <time.h>
#include <malloc.h>
#include <math.h>
#include <stdlib.h>


#define MATDIM 1024



void multiplymat(float *a, float* b, float* ans){
    for (int row=0;row<MATDIM;row++){
        for (int column=0;column<MATDIM;column++){
            int sum = 0;
            for(int i=0;i< MATDIM; i++){
                sum += a[MATDIM * row + i] * b[MATDIM * i + column];
            }
            ans[MATDIM * row + column] = sum;
        }
    }
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


    starttime = clock();
    multiplymat(a, b, ans);
    


    int ww = 0;
    for(int i=0;i<MATDIM;i++){
        for(int j=0;j<MATDIM;j++){
            if(ans[i*MATDIM + j]-MATDIM > 0.01){
                ww += 1;
            }
            
        }
    }
    if(!ww){
        printf("Successful!\n");
    }else{
        printf("Failed with %d wrong elements\n", ww);
    }



    free(a);
    free(b);
    free(ans);
    endtime = clock();
    printf("time: %f", (double)(endtime - starttime)/CLOCKS_PER_SEC);
}