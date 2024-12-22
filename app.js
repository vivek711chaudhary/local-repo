const express = require('express');
const {web3} = require('./web3Config')
const { body, param, validationResult } = require('express-validator');
const rateLimit = require('express-rate-limit');
const {
  startBattle,
  voteTrack,
  getBattleVotes,
  getBattleDetails,
  getTotalVoters,
  getWinner,
  func1,
  getVotersList,
  transferAmount
} = require('./music_battle_contract'); // Assume these functions are connected to the smart contract

const app = express();

// Global object to store votes for leaderboard (simplified for this example)

// Middleware
app.use(express.json());

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});
app.use(limiter);

// Validation middleware for starting battle
const validateBattleStart = [
  body('track1').trim().notEmpty().withMessage('Track 1 is required'),
  body('track2').trim().notEmpty().withMessage('Track 2 is required')
];

// Validation middleware for voting
const validateVote = [
  body('battleId').isNumeric().withMessage('Battle ID must be a number'),
  body('trackNumber').isIn([1, 2]).withMessage('Track number must be 1 or 2')
];

// Validation middleware for retrieving battle details
const validateBattleId = [
  param('battleId').isNumeric().withMessage('Battle ID must be a number')
];

// Middleware to handle validation errors
const handleValidationErrors = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }
  next();
};

// Route to start a battle
app.post(
  '/startbattle',
  validateBattleStart,
  handleValidationErrors,
  async (req, res) => {
    try {
      const { track1, track2,creatorTrack1,creatorTrack2,userAddress,paymentAmount } = req.body;
      const result = await startBattle(track1, track2 ,creatorTrack1, creatorTrack2,userAddress,paymentAmount);

      res.json({
        message: `Music Battle between ${track1} and ${track2} has started!`,
        ...result
      });
    } catch (error) {
      console.error('Battle Start Error:', error);
      res.status(500).json({ error: 'Failed to start battle' });
    }
  }
);


app.post(
  '/votetrack',
  validateVote,
  handleValidationErrors,
  async (req, res) => {
    try {
      const { battleId, trackNumber, userAddress,paymentAmount } = req.body;

      if (!userAddress) {
        return res.status(400).json({ error: 'User address is required' });
      }

      const result = await voteTrack(battleId, trackNumber, userAddress,paymentAmount);



      // Update leaderboard
      // if (trackNumber === 1) {
      //   leaderboard.track1++;
      // } else if (trackNumber === 2) {
      //   leaderboard.track2++;
      // }

      console.log("Inside the vote function :result:",result)

      
      if(result!=undefined){
        res.json({
          message: `Vote registered for Track ${trackNumber}!`,
          ...result
        });
      }
      else{
        res.json({
          message: `Vote already registered for Track ${trackNumber}!`
        });
      }


    } catch (error) {
      console.error('Vote Error:', error);
      res.status(500).json({ error: 'Failed to register vote' });
    }
  }
);





// // Route to get the leaderboard
// app.get('/leaderboard/', (req, res) => {
//   try {
//     const sortedLeaderboard = Object.entries(leaderboard)
//       .sort(([, a], [, b]) => b - a)
//       .map(([track, votes]) => ({ track, votes }));

//     res.json({
//       leaderboard: sortedLeaderboard
//     });
//   } catch (error) {
//     console.error('Leaderboard Error:', error);
//     res.status(500).json({ error: 'Failed to retrieve leaderboard' });
//   }
// });

// Route to get votes for a battle
app.get(
  '/battle/:battleId/votes',
  validateBattleId,
  handleValidationErrors,
  async (req, res) => {
    try {
      const { battleId } = req.params;
      const votes = await getBattleVotes(battleId);

      res.json({
        battleId: parseInt(battleId),
        track1Votes: votes.track1Votes,
        track2Votes: votes.track2Votes
      });
    } catch (error) {
      console.error('Get Votes Error:', error);
      res.status(500).json({ error: 'Failed to retrieve battle votes' });
    }
  }
);

// Route to get battle details
app.get(
  '/leaderboard/:battleId',  // Corrected to accept battleId as a parameter
  validateBattleId,
  handleValidationErrors,
  async (req, res) => {
    try {
      const { battleId } = req.params;
      const votes = await getBattleVotes(battleId);

      // Convert the string votes to numbers (parseInt)
      const leaderboard = [
        { track: 'Track 1', votes: parseInt(votes.track1Votes) },  // Convert to number
        { track: 'Track 2', votes: parseInt(votes.track2Votes) },  // Convert to number
      ];

      // Sort the leaderboard by votes in descending order
      const sortedLeaderboard = leaderboard.sort((a, b) => b.votes - a.votes);

      res.json({
        battleId: parseInt(battleId),
        leaderboard: sortedLeaderboard
      });
    } catch (error) {
      console.error('Get Votes Error:', error);
      res.status(500).json({ error: 'Failed to retrieve battle votes' });
    }
  }
);

// Route to get total voters for a battle
app.get(
  '/battle/:battleId/voters',
  validateBattleId,
  handleValidationErrors,
  async (req, res) => {
    try {
      const { battleId } = req.params;
      const totalVoters = await getTotalVoters(battleId);

      res.json({
        battleId: parseInt(battleId),
        totalVoters
      });
    } catch (error) {
      console.error('Get Voters Error:', error);
      res.status(500).json({ error: 'Failed to retrieve total voters' });
    }
  }
);
app.get(
  '/battle/:battleId/details',
  validateBattleId,
  handleValidationErrors,
  async (req, res) => {
    try {
      const { battleId } = req.params;
      const result = await getBattleDetails(battleId);

      res.json({
        battleId: parseInt(battleId),
        ...result
      });
    } catch (error) {
      console.error('Get Battle Details Error:', error);
      res.status(500).json({ error: 'Failed to get Battle Details' });
    }
  }
);
app.get(
  '/battle/:battleId/votersList',
  validateBattleId,
  handleValidationErrors,
  async (req, res) => {
    try {
      const { battleId } = req.params;
      const votersList = await getVotersList(battleId);

      res.json({
        battleId: parseInt(battleId),
        votersList
      });
    } catch (error) {
      console.error('Get Voters Error:', error);
      res.status(500).json({ error: 'Failed to retrieve total voters' });
    }
  }
);

app.get(
  '/battle/:battleId/winner',
  validateBattleId,
  handleValidationErrors,
  async (req, res) => {
    try {
      const { battleId } = req.params;
      const winner = await getWinner(battleId);

      res.json({
        battleId: parseInt(battleId),
        ...winner
      });
    } catch (error) {
      console.error('Get Winner Error:', error);
      res.status(500).json({ error: 'Failed to retrieve battle winner' });
    }
  }
);
app.get(
  '/balance/',
  handleValidationErrors,
  async (req, res) => {
    try {
      const balance = await func1();

      res.json({
        balance
      });
    } catch (error) {
      console.error('Get Balance Error:', error);
      res.status(500).json({ error: 'Failed to retrieve Account Balance' });
    }
  }
);


// Utility function to validate Ethereum address
function isValidAddress(address) {
    try {
        // Using the newer method to check address validity
        return web3.utils.isHexStrict(address) && address.length === 42;
    } catch (error) {
        return false;
    }
}



// Express API endpoint
app.post('/transferToOwner', handleValidationErrors, async (req, res) => {
    try {
        const { amount, userAddress, senderAddress } = req.body;

        // Input validation
        if (!amount || amount <= 0) {
            return res.status(400).json({ 
                success: false,
                error: 'Invalid amount provided' 
            });
        }

        if (!userAddress || !senderAddress) {
            return res.status(400).json({ 
                success: false,
                error: 'Both recipient and sender addresses are required' 
            });
        }

        // Validate addresses format using the new method
        if (!isValidAddress(userAddress) || !isValidAddress(senderAddress)) {
            return res.status(400).json({ 
                success: false,
                error: 'Invalid Ethereum address format' 
            });
        }

        // Perform the transfer
        const result = transferAmount(amount, userAddress, senderAddress);

        // Send success response
        res.json({
            success: true,
            data: result
        });

    } catch (error) {
        console.error('Transfer Error:', error);
        
        res.status(500).json({ 
            success: false,
            error: error.message || 'Failed to process transfer'
        });
    }
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

// Start the server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Backend running on http://localhost:${PORT}`);
});

module.exports = app;

