'''
Transactions.py
Author: Evan Corriere

Transaction objects represent and individual transaction
taking payment from a UTXO and sending that customer an NFT along 
with the min ADA required. The remaining balance is send to a second address.

Important: must build, calculate fees, and build again before signing and submitting
See "build_sign_submit" method for easy use. 
'''
import subprocess

class Transaction:

    rawTxFile = 'matx.raw'
    protocolFile = 'mainnetuser/protocol.json'
    userSKFile = 'mainnetuser/pay.skey'
    policySKFile = 'policy/policy.skey'
    signedTxFile = 'matx.signed'
    policyScriptFile = 'policy/policy.script'
    #network_args = ['--testnet-magic', '1097911063']
    policyHash = 'REDACTED'
    network_args = ['--mainnet']

    def __init__(self, txHash, txIx, txAmount, destAddr, destAmount, surplusAddr, nftnum):
        '''
            Creates tx to send x amount
        '''
        self.txHash = txHash
        self.txIx = txIx
        self.txAmount = txAmount
        self.destAddr = destAddr
        self.destAmount = destAmount
        self.surplusAddr = surplusAddr
        self.fees = 0
        self.nftnum = nftnum

    def build(self):
        # builds tx with current fees value
        surplusAmount = self.txAmount - self.destAmount - self.fees
        print('amount, surp, destAmt, fees =', self.txAmount, surplusAmount, self.destAmount, self.fees)
        assert surplusAmount >= 0

        build_command = ['cardano-cli', 'transaction', 'build-raw', '--mary-era',
            '--fee', f'{self.fees}', '--tx-in', f'{self.txHash}#{self.txIx}',
            '--tx-out', f'{self.destAddr}+{self.destAmount}+1 {self.policyHash}.Nft{self.nftnum}',
            '--tx-out', f'{self.surplusAddr}+{surplusAmount}',
            '--invalid-hereafter', "40000000",
            f'--mint=1 {self.policyHash}.Nft{self.nftnum}',
            '--metadata-json-file', f'metadata/nft{self.nftnum}.json', '--out-file', self.rawTxFile]
        cmd = subprocess.run(build_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


    def calculate_fees(self):
        # calcualte fees for tx in rawTxFile
        calculate_command = ['cardano-cli', 'transaction', 'calculate-min-fee', 
            '--tx-body-file', self.rawTxFile, '--tx-in-count', '1', '--tx-out-count', '2',
            '--witness-count', '2', '--protocol-params-file', self.protocolFile ]
        cmd = subprocess.run(calculate_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        feeStr = cmd.stdout.decode('utf-8')
        self.fees = int(feeStr.split()[0])

    def sign(self):
        # signs tx
        sign_command = ['cardano-cli', 'transaction', 'sign', '--signing-key-file', self.userSKFile, '--signing-key-file', self.policySKFile,
            '--script-file', self.policyScriptFile,'--tx-body-file', self.rawTxFile, '--out-file', self.signedTxFile] + self.network_args
        cmd = subprocess.run(sign_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    def submit(self):
        # submits
        submit_command = ['cardano-cli', 'transaction', 'submit', '--tx-file', self.signedTxFile] + self.network_args
        cmd = subprocess.run(submit_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    def build_sign_submit(self):
        # Runs tx from start to finish; build, calc fees, rebuild, sign, submit
        self.build()
        self.calculate_fees()
        self.build()
        self.sign()
        self.submit()
