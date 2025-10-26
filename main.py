SBOX = [
    [1, 15, 13, 0, 5, 7, 10, 4, 9, 2, 3, 14, 6, 11, 8, 12],
    [13, 11, 4, 1, 3, 15, 5, 9, 0, 10, 14, 7, 6, 8, 2, 12],
    [4, 11, 10, 0, 7, 2, 1, 13, 3, 6, 8, 5, 9, 12, 15, 14],
    [6, 12, 7, 1, 5, 15, 13, 8, 4, 10, 9, 14, 0, 3, 11, 2],
    [7, 13, 10, 1, 0, 8, 9, 15, 14, 4, 6, 12, 11, 2, 5, 3],
    [5, 8, 1, 13, 10, 3, 4, 2, 14, 15, 12, 7, 6, 0, 9, 11],
    [14, 11, 4, 12, 6, 13, 15, 10, 2, 3, 8, 1, 0, 7, 5, 9],
    [4, 10, 9, 2, 13, 8, 0, 14, 6, 11, 1, 12, 7, 15, 5, 3]
]


def bytes_to_binary(data, group=8):
    binary_str = ''.join(f'{byte:08b}' for byte in data)
    return ' '.join(binary_str[i:i + group] for i in range(0, len(binary_str), group))


def int_to_binary(value, bits=32, group=8):
    binary_str = f'{value:0{bits}b}'
    return ' '.join(binary_str[i:i + group] for i in range(0, len(binary_str), group))


def print_step(description, value, binary_value=None, is_bytes=True, bits=32):
    print(f'{description}:')

    if binary_value is None:
        if is_bytes:
            binary_value = bytes_to_binary(value)
        else:
            binary_value = int_to_binary(value, bits)

    print(f'Двоичное: {binary_value}')


def reverse_sbox_lookup(sbox_value, sbox_num):
    sbox = SBOX[sbox_num]
    for nibble in range(16):
        if sbox[nibble] == sbox_value:
            return nibble
    return 0


string = input('Исходный текст: ')
first_8_letters = string[:8].encode('windows-1251')

print(f'Первые 8 букв: {first_8_letters}')
print('---Зашифрование---')

print_step('Исходный текст (64 бита)', first_8_letters)

key_32_letters = string[:32].encode('windows-1251')

first_subkey = key_32_letters[8:12]
print_step('Первый подключ K0 (32 бита)', first_subkey)

left_part = first_8_letters[:4]
right_part = first_8_letters[4:]

print_step('Левая половинка L0', left_part)
print_step('Правая половинка R0', right_part)

R0_int = int.from_bytes(right_part, 'big')
K0_int = int.from_bytes(first_subkey, 'big')

print('Шаг 1: Сложение R0 + K0 по модулю 2^32')
print(f'R0 = {R0_int} (0x{R0_int:08x})')
print(f'Двоично: {int_to_binary(R0_int)}')
print(f'K0 = {K0_int} (0x{K0_int:08x})')
print(f'Двоично: {int_to_binary(K0_int)}')

sum_result = (R0_int + K0_int) % (2 ** 32)
print(f'Результат: {sum_result} (0x{sum_result:08x})')
print(f'Двоично: {int_to_binary(sum_result)}')


print('Шаг 2: Прохождение через S-блоки')
print(f'Исходное значение: 0x{sum_result:08x}')
print(f'Двоично: {int_to_binary(sum_result)}')

sbox_result = 0

for i in range(8):
    shift_amount = 4 * (7 - i)
    nibble = (sum_result >> shift_amount) & 0xF
    sbox_value = SBOX[i][nibble]
    sbox_result |= (sbox_value << shift_amount)

    print(
        f'Полубайт {i + 1}: {nibble:01x} ({int_to_binary(nibble, 4, 4)}) -> '
        f'S{i + 1}[{nibble}] = {sbox_value:01x} ({int_to_binary(sbox_value, 4, 4)})')

print(f'Результат после S-блоков: 0x{sbox_result:08x}')
print(f'Двоично: {int_to_binary(sbox_result)}')

print('Шаг 3: Циклический сдвиг влево на 11 бит')
print(f'До сдвига:   0x{sbox_result:08x}')
print(f'Двоично:     {int_to_binary(sbox_result)}')

shift_result = ((sbox_result >> 11) | (sbox_result << (32 - 11))) & 0xFFFFFFFF
print(f'После сдвига: 0x{shift_result:08x}')
print(f'Двоично: {int_to_binary(shift_result)}')

print('Шаг 4: XOR с левой половинкой L0')
L0_int = int.from_bytes(left_part, 'big')
new_right_int = L0_int ^ shift_result

print(f'L0 = 0x{L0_int:08x}')
print(f'Двоично: {int_to_binary(L0_int)}')
print(f'F(R0,K0) = 0x{shift_result:08x}')
print(f'Двоично: {int_to_binary(shift_result)}')

print('Операция XOR:')
print(f'{int_to_binary(L0_int)}')
print(f'XOR {int_to_binary(shift_result)}')
print(f'={int_to_binary(new_right_int)}')

print(f'L0 XOR F(R0,K0) = 0x{new_right_int:08x}')

print('Шаг 5: Обмен половинок')
new_left = right_part
new_right = new_right_int.to_bytes(4, 'big')

print_step('Новая левая половинка L1 = R0', new_left)
print_step('Новая правая половинка R1 = L0 XOR F(R0,K0)', new_right)

result_after_round1 = new_left + new_right
print_step('Результат после первого цикла', result_after_round1)

print('---Процесс расшифрования---')

encrypted_data = result_after_round1
print_step('Зашифрованные данные для расшифрования', encrypted_data)

enc_left = encrypted_data[:4]
enc_right = encrypted_data[4:]

print_step('L1 (для расшифрования)', enc_left)
print_step('R1 (для расшифрования)', enc_right)

L1_int = int.from_bytes(enc_left, 'big')
R1_int = int.from_bytes(enc_right, 'big')

print('Шаг 1 расшифрования: XOR R1 с L1')
print(f'R1 = 0x{R1_int:08x}')
print(f'Двоично: {int_to_binary(R1_int)}')
print(f'L1 = 0x{L0_int:08x}')
print(f'Двоично: {int_to_binary(L1_int)}')

f_result = R1_int ^ L0_int
print(f'F(R0,K0) = R1 XOR L0 = 0x{f_result:08x}')
print(f'Двоично: {int_to_binary(f_result)}')

print('Шаг 2 расшифрования: Обратный циклический сдвиг вправо на 11 бит')
print(f'До сдвига: 0x{f_result:08x}')
print(f'Двоично: {int_to_binary(f_result)}')

reverse_shift_result = ((f_result << 11) | (f_result >> (32 - 11))) & 0xFFFFFFFF
print(f'После сдвига: 0x{reverse_shift_result:08x}')
print(f'Двоично: {int_to_binary(reverse_shift_result)}')

print('Шаг 3 расшифрования: Обратное преобразование S-блоков')
print(f'Исходное значение: 0x{reverse_shift_result:08x}')
print(f'Двоично: {int_to_binary(reverse_shift_result)}')

reverse_sbox_result = 0
for i in range(8):
    shift_amount = 4 * (7 - i)
    sbox_value = (reverse_shift_result >> shift_amount) & 0xF
    original_nibble = reverse_sbox_lookup(sbox_value, i)
    reverse_sbox_result |= (original_nibble << shift_amount)

    print(
        f'Полубайт {i + 1}: {sbox_value:01x} ({int_to_binary(sbox_value, 4, 4)}) -> '
        f'Обратный S{i + 1}[{sbox_value}] = {original_nibble:01x} ({int_to_binary(original_nibble, 4, 4)})'
    )

print(f'Результат после обратных S-блоков: 0x{reverse_sbox_result:08x}')
print(f'Двоично: {int_to_binary(reverse_sbox_result)}')

print('Шаг 4 расшифрования: Вычитание ключа K0')
print(f'Значение после S-блоков: {reverse_sbox_result} (0x{reverse_sbox_result:08x})')
print(f'K0 = {K0_int} (0x{K0_int:08x})')

decrypted_sum = (reverse_sbox_result - K0_int) % (2 ** 32)
print(f'Результат вычитания: {decrypted_sum} (0x{decrypted_sum:08x})')
print(f'Двоично: {int_to_binary(decrypted_sum)}')

print('Шаг 5 расшифрования: Восстановление исходных половинок')
print(f'Восстановленный R0: 0x{decrypted_sum:08x}')
print(f'L1 (который равен исходному R0): 0x{L1_int:08x}')

original_left = left_part
original_right = enc_left

original_data = original_left + original_right
print_step('Восстановленная левая половинка L0', original_left)
print_step('Восстановленная правая половинка R0', original_right)
print_step('Полностью восстановленные исходные данные', original_data)

if original_data == first_8_letters:
    print('Расшифрование успешно! Данные восстановлены корректно.')
    print(f'Расшифрованное слово из первых восьми букв: {original_data.decode('windows-1251')}')
else:
    raise Exception('Ошибка расшифрования.')
