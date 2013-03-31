__kernel void code(__global float* a, __global float* b)
{
    unsigned int i = get_global_id(0);
    b[i] = a[i];
}
