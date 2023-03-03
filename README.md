# spectrum scanner

SDR based spectrum scanner

Anaconda set up:

1. Create and activate new environment:
    ```
    conda create -n adi_hw python=3.9
    conda activate adi_hw
    ```
2. Add conda-forge channels:
    ```
    conda config --add channels conda-forge
    ```
3. Install packages:
    ```
    conda install numpy scipy matplotlib libiio pyadi-iio ipykernel
    ```
    or
    ```
    conda env update --file requirements.yml
    ```
4. Install conda env as ipykernel:
    ```
    python -m ipykernel install --user --name=adi_hw
    ```

5. Launch Jupyter Notebook or Lab and select created kernel.