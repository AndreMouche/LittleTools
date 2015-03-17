#for i in {1..9}; do echo $i;cp orign/myphoto_$i.jpg jpgs/myphoto_0$i.jpg;done 
#for i in {10..51}; do echo $i;cp orign/myphoto_$i.jpg jpgs/myphoto_$i.jpg;done 
for i in {1..9}; do echo $i;cwebp orign/myphoto_$i.jpg  -q 85 -o jpg_to_webps/myphoto_0$i.webp; done
for i in {10..51}; do echo $i;cwebp orign/myphoto_$i.jpg  -q 85 -o jpg_to_webps/myphoto_$i.webp; done
for i in {1..9}; do echo $i;bpgenc orign/myphoto_$i.jpg -q 27 -o jpg_to_bpgs/myphoto_0$i.bpg; done
for i in {10..51}; do echo $i;bpgenc orign/myphoto_$i.jpg -q 27 -o jpg_to_bpgs/myphoto_$i.bpg; done 
