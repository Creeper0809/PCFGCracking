class TrainingDataParser:
    def __init__(self,min_length: int,max_length : int,filedir : str,encoding : str = "utf-8"):
        self.min_length = min_length
        self.max_length = max_length
        self.filedir = filedir
        self.encoding = encoding
        self.file = open(
            self.filedir,
            "r",
            encoding = self.encoding)
        self.num_passwords = 0

    def check_valid(self,input_password):
        '''
        비밀번호 유효성 검사
        :param input_password:
        :return: boolean
        '''
        if len(input_password) < self.min_length:
            return False
        if len(input_password) > self.max_length:
            return False
        if "\t" in input_password:
            return False

        for invalid_hex in range(0x0, 0x20):
            if chr(invalid_hex) in input_password:
                return False

        if u"\u2028" in input_password:
            return False

        if u"\u0085" in input_password:
            return False

        return True

    def read_password(self):
        try:
            while True:
                try:
                    password = self.file.readline()
                except UnicodeError:
                    continue

                self.num_passwords += 1

                if password == "":
                    self.file.close()
                    return

                # 잡다한거 날리기
                clean_password = password.rstrip('\r\n')

                # $HEX[]형식의 패스워드 디코드
                if clean_password.startswith("$HEX[") and clean_password.endswith("]"):
                    try:
                        clean_password = bytes.fromhex(clean_password[5:-1]).decode(self.encoding)
                    except:
                        continue

                try:
                    clean_password.encode(self.encoding)
                except UnicodeEncodeError as msg:
                    print(msg)
                    continue

                # 패스워드 유효성 검사
                if not self.check_valid(clean_password):
                    continue

                yield clean_password

        except IOError as error:
            print (error)
            print ("Error reading file " + self.filename)
            raise
