contract EthDig
{
    uint constant LifeTime = 30;
    
    address Owner = msg.sender;
    address OutputAddress = msg.sender;
    
    uint64 Coef1=723;
    uint64 Coef2=41665;
    uint64 Coef3=600000;
    
    uint public ContributedAmount;
    uint ContributedLimit = 10 ether;
    
    uint public CashForHardwareReturn;
    uint public FreezedCash;
    
    uint16 UsersLength = 0;
    mapping (uint16 =&gt; User) Users;
    struct User{
        address Address;
        uint16 ContributionsLength;
        mapping (uint16 =&gt; Contribution) Contributions;
    }
    struct Contribution{
        uint CashInHarware;
        uint CashFreezed;
        
        uint16 ProfitPercent;
        uint NeedPayByDay;
        
        bool ReuseCashInHarware;
        
        uint DateCreated;
        uint DateLastCheck;
        uint AlreadyPaid;
        
        bool ReturnedHardwareCash;
        bool Finished;
    }
    
    function  ContributeInternal(uint16 userId,uint cashInHarware,uint cashFreezed,bool reuseCashInHarware) private{
        Contribution contribution = Users[userId].Contributions[Users[userId].ContributionsLength];

        contribution.CashInHarware = cashInHarware;
        contribution.CashFreezed = cashFreezed;
        
        uint8 noFreezCoef = uint8 ((cashInHarware * 100) / (cashFreezed+cashInHarware));
        contribution.ProfitPercent = uint16 (((Coef1 * noFreezCoef * noFreezCoef) + (Coef2 * noFreezCoef) + Coef3)/10000);//10000
        
        contribution.NeedPayByDay = (((cashInHarware + cashFreezed) /10000) * contribution.ProfitPercent)/LifeTime;
        contribution.ReuseCashInHarware = reuseCashInHarware;
        contribution.DateCreated = now;
        contribution.DateLastCheck = now;
        
        Users[userId].ContributionsLength++;
    }
    function ContributeWithSender (bool reuseCashInHarware,uint8 freezeCoeff,address sender) {
        if (msg.value == 0 || freezeCoeff&gt;100 ||ContributedAmount + msg.value &gt; ContributedLimit)
        {
            sender.send(msg.value);
            return;
        }
        
        uint16 userId = GetUserIdByAddress(sender);
        if (userId == 65535)
        {
            userId = UsersLength;
            Users[userId].Address = sender;
            UsersLength ++;
        }
        
        uint cashFreezed = ((msg.value/100)*freezeCoeff);
        ContributeInternal(
            userId,
            msg.value - cashFreezed,
            cashFreezed,
            reuseCashInHarware
            );
        FreezedCash += cashFreezed;
        ContributedAmount += msg.value;
        
        OutputAddress.send(msg.value - cashFreezed);
    }
    function Contribute (bool reuseCashInHarware,uint8 freezeCoeff) {
        ContributeWithSender(reuseCashInHarware,freezeCoeff,msg.sender);
    }
    function ChangeReuseCashInHarware(bool newValue,uint16 userId,uint16 contributionId){
        if (msg.sender != Users[userId].Address) return;
        Users[userId].Contributions[contributionId].ReuseCashInHarware = newValue;
    }
    
    function Triger(){
        if (Owner != msg.sender) return;
        
        uint MinedTillLastPayment = this.balance - CashForHardwareReturn - FreezedCash;
        bool NotEnoughCash = false;
        
        for(uint16 i=0;i&lt;UsersLength;i++)
        {
            for(uint16 j=0;j&lt;Users[i].ContributionsLength;j++)
            {
                Contribution contribution = Users[i].Contributions[j];
                if (contribution.Finished || now - contribution.DateLastCheck &lt; 1 days) continue;
                
                if (contribution.AlreadyPaid != contribution.NeedPayByDay * LifeTime)
                {
                    uint8 daysToPay = uint8((now - contribution.DateCreated)/1 days);
                    if (daysToPay&gt;LifeTime) daysToPay = uint8(LifeTime);
                    uint needToPay = (daysToPay * contribution.NeedPayByDay) - contribution.AlreadyPaid;
                    
                    if (MinedTillLastPayment &lt; needToPay)
                    {
                        NotEnoughCash = true;
                    }
                    else
                    {
                        if (needToPay &gt; 100 finney || daysToPay == LifeTime)
                        {
                            MinedTillLastPayment -= needToPay;
                            Users[i].Address.send(needToPay);
                            contribution.AlreadyPaid += needToPay;
                        }
                    }
                    contribution.DateLastCheck = now;
                }

                if (now &gt; contribution.DateCreated + (LifeTime * 1 days) &amp;&amp; !contribution.ReturnedHardwareCash)
                {
                    if (contribution.ReuseCashInHarware)
                    {
                        ContributeInternal(
                            i,
                            contribution.CashInHarware,
                            contribution.CashFreezed,
                            true
                        );
                        contribution.ReturnedHardwareCash = true;
                    }
                    else
                    {
                        if (CashForHardwareReturn &gt;= contribution.CashInHarware)
                        {
                            CashForHardwareReturn -= contribution.CashInHarware;
                            FreezedCash -= contribution.CashFreezed;
                            ContributedAmount -= contribution.CashFreezed + contribution.CashInHarware;
                            Users[i].Address.send(contribution.CashInHarware + contribution.CashFreezed);
                            contribution.ReturnedHardwareCash = true;
                        }
                    }
                }
                
                if (contribution.ReturnedHardwareCash &amp;&amp; contribution.AlreadyPaid == contribution.NeedPayByDay * LifeTime)
                {
                    contribution.Finished = true;
                }
            }  
        }
        
        if (!NotEnoughCash)
        {
            OutputAddress.send(MinedTillLastPayment);
        }
    }
    
    function ConfigureFunction(address outputAddress,uint contributedLimit,uint16 coef1,uint16 coef2,uint16 coef3)
    {
        if (Owner != msg.sender) return;
        OutputAddress = outputAddress;
        ContributedLimit = contributedLimit;
        Coef1 = coef1;
        Coef2 = coef2;
        Coef3 = coef3;
    }
    
    function SendCashForHardwareReturn(){
        CashForHardwareReturn += msg.value;
    }
    function WithdrawCashForHardwareReturn(uint amount){
        if (Owner != msg.sender || CashForHardwareReturn &lt; amount) return;
        Owner.send(amount);
    }
    
    function GetUserIdByAddress (address userAddress) returns (uint16){
        for(uint16 i=0; i&lt;UsersLength;i++)
        {
            if (Users[i].Address == userAddress)
                return i;
        }
        return 65535;
    }
    
    function GetContributionInfo (uint16 userId,uint16 contributionId) 
    returns (uint a1,uint a2, uint16 a3,uint a4, bool a5,uint a6,uint a7,uint a8,bool a9,bool a10,address a11) 
    {
        Contribution contribution = Users[userId].Contributions[contributionId];
        a1 = contribution.CashInHarware;
        a2 = contribution.CashFreezed;
        a3 = contribution.ProfitPercent;
        a4 = contribution.NeedPayByDay;
        a5 = contribution.ReuseCashInHarware;
        a6 = contribution.DateCreated;
        a7 = contribution.DateLastCheck;
        a8 = contribution.AlreadyPaid;
        a9 = contribution.ReturnedHardwareCash;
        a10 = contribution.Finished;
        a11 = Users[userId].Address;
    }
    
}

contract EthDigProxy
{
    address Owner = msg.sender;
    EthDig public ActiveDigger; 
    
    function ChangeActiveDigger(address activeDiggerAddress){
        if (msg.sender != Owner) return;
        ActiveDigger =EthDig(activeDiggerAddress);
    }
    function GetMoney(){
        if (msg.sender != Owner) return;
        Owner.send(this.balance);
    }
    
    function Contribute (bool reuseCashInHarware,uint8 freezeCoeff) {
        ActiveDigger.ContributeWithSender.value(msg.value)(reuseCashInHarware,freezeCoeff,msg.sender);
    }
    function (){
        ActiveDigger.ContributeWithSender.value(msg.value)(false,0,msg.sender);
    }
}